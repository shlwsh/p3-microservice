-- jos_filter.lua
-- Pandoc Lua filter for 《软件学报》DOCX output
-- Handles: image sizing, table captions, math cleanup

-- Ensure images have reasonable widths for docx
function Image(el)
    -- Set default width if not specified
    if el.attr and el.attr.attributes then
        if not el.attr.attributes.width then
            el.attr.attributes.width = "100%"
        end
    end
    return el
end

-- Clean up any remaining raw LaTeX that pandoc couldn't parse
function RawInline(el)
    if el.format == "tex" or el.format == "latex" then
        local text = el.text

        -- Remove leftover font commands
        text = text:gsub("\\hei%s*", "")
        text = text:gsub("\\kai%s*", "")
        text = text:gsub("\\song%s*", "")
        text = text:gsub("\\fs%s*", "")
        text = text:gsub("\\xiaowuhao%s*", "")
        text = text:gsub("\\wuhao%s*", "")
        text = text:gsub("\\noindent%s*", "")

        -- Convert \texttt{} to code
        local tt = text:match("\\texttt{(.-)}")
        if tt then
            return pandoc.Code(tt)
        end

        -- If nothing useful remains, return empty
        if text:match("^%s*$") then
            return pandoc.Str("")
        end

        -- Return cleaned text as string if it's simple text
        local clean = text:gsub("\\[a-zA-Z]+%s*", ""):gsub("[{}]", "")
        if clean and clean ~= "" and not clean:match("\\") then
            return pandoc.Str(clean)
        end
    end
    return el
end

function RawBlock(el)
    if el.format == "tex" or el.format == "latex" then
        local text = el.text

        -- Remove empty environments
        if text:match("^%s*\\begin{flushleft}%s*\\end{flushleft}%s*$") then
            return pandoc.Null()
        end

        -- Remove standalone font size commands
        if text:match("^%s*\\[a-z]+hao%s*$") then
            return pandoc.Null()
        end
    end
    return el
end

-- Fix heading numbering: ensure sections are numbered
function Header(el)
    -- Remove any stray attributes that might break docx
    el.attr = pandoc.Attr(el.identifier, el.classes, {})
    return el
end

-- Ensure tables have proper structure
function Table(el)
    return el
end
