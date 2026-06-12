#!/usr/bin/env python3
"""
Preprocess main-jos.tex into a Pandoc-friendly standalone .tex file.

Resolves:
  - \\input{} expansion
  - \\newcommand macro inline expansion (AbstractContentZh/En, KeywordsZh/En)
  - Custom rjthesis commands → standard LaTeX
  - Font size commands removal (handled by reference template)
  - PDF figures → PNG conversion
  - algorithm2e → code-block fallback
  - \\cite → inline from .bbl
  - Cross-references \\ref → placeholder text
"""
import os
import re
import sys
import subprocess
import argparse
from pathlib import Path


def convert_pdf_to_png(pdf_path: str, png_path: str, dpi: int = 300) -> bool:
    """Convert a PDF figure to PNG using pdftoppm."""
    if os.path.exists(png_path):
        return True
    try:
        # pdftoppm outputs <prefix>-1.png for single page PDFs
        prefix = png_path.replace('.png', '')
        subprocess.run(
            ['pdftoppm', '-png', '-r', str(dpi), '-singlefile', pdf_path, prefix],
            check=True, capture_output=True
        )
        return os.path.exists(png_path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def read_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_newcommands(tex: str) -> dict:
    """Extract \\newcommand definitions for known macros."""
    macros = {}
    # Match \newcommand{\Name}{content} including multi-line with %
    pattern = r'\\newcommand\{\\(\w+)\}\{%\n(.*?)\n\}'
    for m in re.finditer(pattern, tex, re.DOTALL):
        name = m.group(1)
        body = m.group(2).rstrip('%').strip()
        macros[name] = body

    # Also match single-line \newcommand{\Name}{content}
    pattern2 = r'\\newcommand\{\\(\w+)\}\{([^}]+)\}'
    for m in re.finditer(pattern2, tex):
        name = m.group(1)
        if name not in macros:
            macros[name] = m.group(2).strip()

    return macros


def expand_inputs(tex: str, base_dir: str) -> str:
    """Recursively expand \\input{file} directives."""
    def replace_input(m):
        fname = m.group(1)
        if not fname.endswith('.tex'):
            fname += '.tex'
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            content = read_file(fpath)
            # Recursively expand
            content = expand_inputs(content, os.path.dirname(fpath))
            return content
        else:
            return f'% [WARNING] File not found: {fname}\n'

    return re.sub(r'\\input\{([^}]+)\}', replace_input, tex)


def parse_bbl(bbl_path: str) -> dict:
    """Parse .bbl file into a dict of cite_key → formatted text."""
    if not os.path.exists(bbl_path):
        return {}

    bbl = read_file(bbl_path)
    # Remove the thebibliography environment markers
    bbl = re.sub(r'\\begin\{thebibliography\}\{[^}]*\}', '', bbl)
    bbl = re.sub(r'\\end\{thebibliography\}', '', bbl)

    entries = {}
    # Split on \bibitem
    parts = re.split(r'\\bibitem\{(\w+)\}', bbl)
    # parts[0] is before first bibitem, then alternating key, content
    for i in range(1, len(parts) - 1, 2):
        key = parts[i]
        content = parts[i + 1].strip()
        # Clean up LaTeX formatting
        content = re.sub(r'\\newblock\s*', '', content)
        # Handle special chars before blanket brace removal
        content = re.sub(r'\\c\{c\}', 'ç', content)
        content = re.sub(r'\{\\em\s+', '', content)
        # Remove ALL braces (both { and })
        content = content.replace('{', '').replace('}', '')
        # Remove remaining LaTeX commands
        content = re.sub(r'\\[a-zA-Z]+\s*', '', content)
        content = re.sub(r'et~al\.', 'et al.', content)
        content = re.sub(r'~', ' ', content)
        content = re.sub(r'\s+', ' ', content).strip()
        if content:
            entries[key] = content

    return entries


def build_ref_list_from_bbl(bbl_path: str) -> str:
    """Build a pandoc-friendly reference list from .bbl."""
    entries = parse_bbl(bbl_path)
    if not entries:
        return ''

    lines = ['\n\n\\section*{参考文献}\n']
    for i, (key, text) in enumerate(entries.items(), 1):
        lines.append(f'\\noindent [{i}] {text}\n')

    return '\n'.join(lines)


def resolve_cites(tex: str, bbl_entries: dict, cite_counter: list) -> str:
    """Replace \\cite{keys} with [N,M,...] numbers."""
    if not bbl_entries:
        return tex

    # Build key → number mapping
    key_to_num = {}
    for i, key in enumerate(bbl_entries.keys(), 1):
        key_to_num[key] = i

    def replace_cite(m):
        keys = [k.strip() for k in m.group(1).split(',')]
        nums = []
        for k in keys:
            if k in key_to_num:
                nums.append(str(key_to_num[k]))
            else:
                nums.append(f'?{k}')
        return '[' + ','.join(nums) + ']'

    tex = re.sub(r'\\cite\{([^}]+)\}', replace_cite, tex)
    return tex


def resolve_refs(tex: str) -> str:
    """Replace \\ref{label} with placeholder numbers and ~ with space."""
    # Collect label assignments from the text
    labels = {}
    # For figures
    fig_counter = [0]
    def count_fig_label(m):
        fig_counter[0] += 1
        labels[m.group(1)] = str(fig_counter[0])
        return ''
    re.sub(r'\\label\{fig:(\w+)\}', count_fig_label, tex)

    # For tables
    tab_counter = [0]
    def count_tab_label(m):
        tab_counter[0] += 1
        labels[m.group(1)] = str(tab_counter[0])
        return ''
    re.sub(r'\\label\{tab:(\w+)\}', count_tab_label, tex)

    # For algorithms
    alg_counter = [0]
    def count_alg_label(m):
        alg_counter[0] += 1
        labels[m.group(1)] = str(alg_counter[0])
        return ''
    re.sub(r'\\label\{alg:(\w+)\}', count_alg_label, tex)

    # For equations
    eq_counter = [0]
    def count_eq_label(m):
        eq_counter[0] += 1
        labels[m.group(1)] = str(eq_counter[0])
        return ''
    re.sub(r'\\label\{eq:(\w+)\}', count_eq_label, tex)

    # Now replace references
    section_counter = [0]
    for m in re.finditer(r'\\section\{', tex):
        section_counter[0] += 1

    # Generic label collector
    all_labels = {}
    counter = {'fig': 0, 'tab': 0, 'alg': 0, 'eq': 0, 'sec': 0}
    prefix_map = {'fig': '图', 'tab': '表', 'alg': '算法', 'eq': '式'}

    for m in re.finditer(r'\\label\{(\w+):(\w+)\}', tex):
        prefix = m.group(1)
        name = m.group(2)
        key = f'{prefix}:{name}'
        if prefix in counter:
            counter[prefix] += 1
            all_labels[key] = str(counter[prefix])

    def replace_ref(m):
        full = m.group(0)
        label = m.group(1)
        if label in all_labels:
            return all_labels[label]
        return '??'

    tex = re.sub(r'\\ref\{([^}]+)\}', replace_ref, tex)
    return tex


def clean_algorithm_env(tex: str) -> str:
    """Convert algorithm2e environments to markdown-friendly code blocks."""
    def replace_algo(m):
        content = m.group(1)
        # Extract caption
        caption_m = re.search(r'\\caption\{([^}]+)\}', content)
        caption = caption_m.group(1) if caption_m else '算法'
        # Extract label
        label_m = re.search(r'\\label\{([^}]+)\}', content)

        # Clean up algorithm commands
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('\\caption') or line.startswith('\\label'):
                continue
            if line.startswith('\\KwIn'):
                val = re.search(r'\\KwIn\{(.+)\}', line)
                if val:
                    clean_lines.append(f'输入: {val.group(1)}')
                continue
            if line.startswith('\\KwOut'):
                val = re.search(r'\\KwOut\{(.+)\}', line)
                if val:
                    clean_lines.append(f'输出: {val.group(1)}')
                continue
            # Clean algorithmic commands
            line = re.sub(r'\\ForEach\{(.+?)\}\{', r'for each \1 do', line)
            line = re.sub(r'\\If\{(.+?)\}\{', r'if \1 then', line)
            line = re.sub(r'\\Return\{(.+?)\}', r'return \1', line)
            line = re.sub(r'\\tcp\*?\{(.+?)\}', r'  // \1', line)
            line = line.replace('\\;', '')
            line = line.replace('\\leftarrow', '←')
            line = line.replace('\\emptyset', '∅')
            line = line.replace('\\cdot', '·')
            line = line.replace('\\mathrm{', '').replace('}', '')
            line = line.replace('\\textbf{or}', 'or')
            line = line.replace('\\textbf{and}', 'and')
            if line.strip():
                clean_lines.append(line)

        result = f'\n\\textbf{{{caption}}}\n\n\\begin{{verbatim}}\n'
        result += '\n'.join(clean_lines)
        result += '\n\\end{verbatim}\n'
        return result

    tex = re.sub(
        r'\\begin\{algorithm\}\[htbp\]\s*(.*?)\\end\{algorithm\}',
        replace_algo, tex, flags=re.DOTALL
    )
    return tex


def clean_table_env(tex: str) -> str:
    """Convert LaTeX tables to Pandoc-friendly format."""
    # Remove \resizebox wrappers and their matching closing braces
    # Pattern: \resizebox{width}{height}{% ... \end{tabular}% }
    # We need to remove both the opening \resizebox{...}{...}{% and the closing }
    tex = re.sub(
        r'\\resizebox\{[^}]*\}\{[^}]*\}\{%?\s*(\\begin\{tabular\}.*?\\end\{tabular\})%?\s*\}',
        r'\1',
        tex, flags=re.DOTALL
    )
    # Fallback: remove any remaining \resizebox wrappers
    tex = re.sub(r'\\resizebox\{[^}]*\}\{[^}]*\}\{%?\s*', '', tex)

    # Remove stray closing braces after \end{tabular} that were from resizebox
    tex = re.sub(r'(\\end\{tabular\})%?\s*\n\s*\}', r'\1', tex)

    # Convert table* to table
    tex = tex.replace('\\begin{table*}', '\\begin{table}')
    tex = tex.replace('\\end{table*}', '\\end{table}')

    return tex


def clean_figure_env(tex: str, figures_dir: str, output_dir: str) -> str:
    """Process figures: convert PDF→PNG and fix paths."""

    def replace_includegraphics(m):
        options = m.group(1) or ''
        filename = m.group(2)

        # Determine source path
        if not os.path.splitext(filename)[1]:
            filename += '.pdf'

        # Try to find the file
        src = os.path.join(figures_dir, filename)
        if not os.path.exists(src):
            # Try without extension, look for png
            base = os.path.splitext(filename)[0]
            png_src = os.path.join(figures_dir, base + '.png')
            if os.path.exists(png_src):
                return f'\\includegraphics[{options}]{{{png_src}}}'

        # Convert PDF to PNG
        if filename.endswith('.pdf'):
            base = os.path.splitext(filename)[0]
            png_name = base + '.png'
            png_path = os.path.join(figures_dir, png_name)

            if os.path.exists(png_path) or convert_pdf_to_png(src, png_path):
                return f'\\includegraphics[{options}]{{{png_path}}}'

        return f'\\includegraphics[{options}]{{{src}}}'

    tex = re.sub(
        r'\\includegraphics\[([^\]]*)\]\{([^}]+)\}',
        replace_includegraphics, tex
    )
    return tex


def strip_custom_commands(tex: str) -> str:
    """Remove/replace rjthesis-specific commands."""

    # Remove preamble-level commands entirely
    preamble_cmds = [
        r'\\PassOptionsToClass\{[^}]*\}\{[^}]*\}',
        r'\\documentclass\{[^}]*\}',
        r'\\usepackage(\[[^\]]*\])?\{[^}]*\}',
        r'\\graphicspath\{[^}]*\}',
        r'\\hypersetup\{[^}]*\}',
        r'\\providecommand\{[^}]*\}\{[^}]*\}',
        r'\\bibliographystyle\{[^}]*\}',
        r'\\bibliography\{[^}]*\}',
        r'\\pagestyle\{[^}]*\}',
        r'\\rjhead\{[^}]*\}',
        r'\\rjcategory\{[^}]*\}',
        r'\\rjtitle\{[^}]*\}',
        r'\\rjauthor\{[^}]*\}',
        r'\\rjinfor\{[^}]*\}',
        r'\\rjmaketitle',
        r'\\rjkeywords\{[^}]*\}',
        r'\\fancyhead\[[^\]]*\]\{[^}]*\}',
        r'\\let\\thefootnote[^\n]*\n',
        r'\\renewcommand\{\\baselinestretch\}\{[^}]*\}',
    ]
    for pat in preamble_cmds:
        tex = re.sub(pat, '', tex)

    # Remove font-size commands (keep content)
    font_sizes = [
        'chuhao', 'xiaochuhao', 'yihao', 'erhao', 'xiaoerhao',
        'sanhao', 'sihao', 'xiaosihao', 'wuhao', 'xiaowuhao',
        'liuhao', 'qihao'
    ]
    for fs in font_sizes:
        tex = re.sub(rf'\\{fs}\b\s*', '', tex)
        tex = re.sub(rf'\{{\\{fs}\s*', '{', tex)

    # Map font-family commands to standard equivalents
    # \hei{text} or {\hei text} → \textbf{text}
    tex = re.sub(r'\{\\hei\s+([^}]*)\}', r'\\textbf{\1}', tex)
    tex = re.sub(r'\\hei\b\s*', '', tex)  # standalone \hei

    # \kai → \textit for emphasis distinction
    tex = re.sub(r'\{\\kai\s+([^}]*)\}', r'\\textit{\1}', tex)
    tex = re.sub(r'\{\\kai\s*', '{', tex)
    tex = re.sub(r'\\kai\b\s*', '', tex)

    # \song → just remove (default font)
    tex = re.sub(r'\{\\song\s+([^}]*)\}', r'\1', tex)
    tex = re.sub(r'\\song\b\s*', '', tex)

    # \fs (fangsong) → remove
    tex = re.sub(r'\{\\fs\s+([^}]*)\}', r'\1', tex)
    tex = re.sub(r'\\fs\b\s*', '', tex)

    # Remove \zihao{N}
    tex = re.sub(r'\\zihao\{[^}]*\}', '', tex)
    # Remove \fontsize{...}{...}\selectfont
    tex = re.sub(r'\\fontsize\{[^}]*\}\{[^}]*\}\\selectfont', '', tex)

    # Remove \hspace{...}
    tex = re.sub(r'\\hspace\{[^}]*\}', ' ', tex)

    # Remove rjabstract environment markers (content already expanded)
    tex = re.sub(r'\\begin\{rjabstract\}', '', tex)
    tex = re.sub(r'\\end\{rjabstract\}', '', tex)

    # Remove flushleft environments
    tex = re.sub(r'\\begin\{flushleft\}', '', tex)
    tex = re.sub(r'\\end\{flushleft\}', '', tex)

    # Remove \vspace
    tex = re.sub(r'\\vspace\{[^}]*\}', '', tex)

    # Remove \noindent
    tex = tex.replace('\\noindent', '')

    # Remove empty braces
    tex = re.sub(r'\{\s*\}', '', tex)

    # Remove % !TEX comments
    tex = re.sub(r'^%\s*!TEX.*$', '', tex, flags=re.MULTILINE)

    # Clean up multiple blank lines
    tex = re.sub(r'\n{3,}', '\n\n', tex)

    return tex


def build_yaml_header(macros: dict, title: str, author: str) -> str:
    """Build YAML metadata block for Pandoc."""
    abstract_zh = macros.get('AbstractContentZh', '')
    abstract_en = macros.get('AbstractContentEn', '')
    keywords_zh = macros.get('KeywordsZh', '')
    keywords_en = macros.get('KeywordsEn', '')

    # Clean LaTeX from abstracts
    for cmd in ['\\cite{', '\\textbf{', '\\textit{', '\\url{']:
        pass  # keep these, pandoc handles them

    yaml = f'''---
title: "{title}"
author:
  - 石洪雷
  - 赵涓涓
institute: "太原理工大学，山西 太原，030024"
abstract: |
  {abstract_zh}
keywords: [{keywords_zh}]
---

'''
    return yaml


def extract_body(tex: str) -> str:
    """Extract content between \\begin{{document}} and \\end{{document}}."""
    m = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', tex, re.DOTALL)
    if m:
        return m.group(1)
    return tex


def remove_metadata_blocks(tex: str) -> str:
    """Remove the title/author/abstract blocks that are in YAML header."""
    # Remove everything before first \section or \input that leads to a section
    # Remove the rjmaketitle block
    tex = re.sub(r'\\rjmaketitle.*?(?=\\section|\\input)', '', tex, flags=re.DOTALL)

    # Remove English title/author/abstract block (between 英文标题 comment and 正文 comment)
    tex = re.sub(
        r'%\s*-+\s*引用格式.*?%\s*-+\s*正文',
        '% ---------- 正文',
        tex, flags=re.DOTALL
    )
    tex = re.sub(
        r'%\s*-+\s*英文标题.*?%\s*-+\s*正文',
        '% ---------- 正文',
        tex, flags=re.DOTALL
    )
    tex = re.sub(
        r'%\s*-+\s*英文摘要.*?%\s*-+\s*正文',
        '% ---------- 正文',
        tex, flags=re.DOTALL
    )

    # Remove the Chinese abstract block (already in YAML)
    tex = re.sub(r'\\AbstractContentZh', '', tex)
    tex = re.sub(r'\\AbstractContentEn', '', tex)
    tex = re.sub(r'\\KeywordsZh', '', tex)
    tex = re.sub(r'\\KeywordsEn', '', tex)

    # Remove the 附中文参考文献 section (duplicate of bibliography)
    tex = re.sub(
        r'%\s*-+\s*附中文参考文献.*?\\end\{description\}\s*\}',
        '', tex, flags=re.DOTALL
    )

    # Remove 作者简介 section
    tex = re.sub(
        r'%\s*-+\s*作者简介.*?\\endgroup',
        '', tex, flags=re.DOTALL
    )

    # Remove LLM usage note
    tex = re.sub(
        r'本文撰写与实验脚本生成过程中.*?负责。',
        '', tex
    )

    return tex


def main():
    parser = argparse.ArgumentParser(description='Preprocess LaTeX for Pandoc DOCX conversion')
    parser.add_argument('--input', default='latex/main-jos.tex', help='Input .tex file')
    parser.add_argument('--output', default=None, help='Output .tex file')
    parser.add_argument('--figures-dir', default='figures', help='Figures directory')
    parser.add_argument('--bbl', default='latex/main-jos.bbl', help='BBL file path')
    parser.add_argument('--root', default='.', help='Project root directory')
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    tex_path = os.path.join(root, args.input)
    figures_dir = os.path.join(root, args.figures_dir)
    bbl_path = os.path.join(root, args.bbl)

    if args.output:
        out_path = os.path.join(root, args.output)
    else:
        out_path = tex_path.replace('.tex', '_pandoc.tex')

    print(f'Reading {tex_path}...')
    tex = read_file(tex_path)

    # 1. Parse macros from abstract file
    abstract_path = os.path.join(root, 'latex/sections/zh/00_abstract.tex')
    if os.path.exists(abstract_path):
        abstract_tex = read_file(abstract_path)
        macros = parse_newcommands(abstract_tex)
    else:
        macros = {}
    print(f'  Found {len(macros)} macros: {list(macros.keys())}')

    # 2. Expand \input directives
    tex_dir = os.path.dirname(tex_path)
    tex = expand_inputs(tex, tex_dir)
    print(f'  Expanded inputs')

    # 3. Extract document body
    tex = extract_body(tex)

    # 4. Inline macro expansions
    for name, body in macros.items():
        tex = tex.replace(f'\\{name}', body)
    print(f'  Inlined macros')

    # 5. Remove metadata blocks (will be in YAML header)
    tex = remove_metadata_blocks(tex)

    # 6. Parse .bbl for citation resolution
    bbl_entries = parse_bbl(bbl_path)
    print(f'  Parsed {len(bbl_entries)} bibliography entries from .bbl')

    # 7. Resolve \\cite references
    tex = resolve_cites(tex, bbl_entries, [0])

    # 8. Resolve \\ref cross-references
    tex = resolve_refs(tex)

    # 9. Handle algorithm environments
    tex = clean_algorithm_env(tex)

    # 10. Handle table environments
    tex = clean_table_env(tex)

    # 11. Handle figures (PDF→PNG)
    tex = clean_figure_env(tex, figures_dir, os.path.dirname(out_path))
    print(f'  Processed figures')

    # 12. Strip custom commands
    tex = strip_custom_commands(tex)

    # 13. Build LaTeX preamble with metadata
    title = '网关流量驱动的微服务定向日志采集框架'
    abstract_zh = macros.get('AbstractContentZh', '')
    # Clean LaTeX math from abstract for cleaner output
    abstract_clean = abstract_zh.replace('\\,', ' ')

    preamble = f"""\\documentclass{{article}}
\\usepackage{{amsmath}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\title{{{title}}}
\\author{{石洪雷 \\and 赵涓涓}}
\\date{{}}
"""

    # 14. Build reference list
    ref_list = build_ref_list_from_bbl(bbl_path)

    # 15. Assemble final document
    body = tex + ref_list
    # Remove any stray \begin/\end{document}
    body = re.sub(r'\\begin\{document\}', '', body)
    body = re.sub(r'\\end\{document\}', '', body)

    # Add abstract
    abstract_block = f"""
\\begin{{abstract}}
{abstract_clean}
\\end{{abstract}}
"""

    final = preamble + '\n\\begin{document}\n\\maketitle\n' + abstract_block + body + '\n\\end{document}\n'

    # 16. Final cleanup
    final = re.sub(r'\n{3,}', '\n\n', final)

    # Write output
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(final)

    print(f'Output written to {out_path}')
    print(f'  Total length: {len(final)} chars')


if __name__ == '__main__':
    main()

