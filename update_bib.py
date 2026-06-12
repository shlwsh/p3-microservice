import re

with open('latex/references.bib', 'r', encoding='utf-8') as f:
    content = f.read()

updates = {
    'bao2023aiops': {
        'title': '{智能运维的实践: 现状与标准化 [Practice of AIOps: Status Quo and Standardization]}',
        'author': '{包航宇 and 殷康璘 and 曹立 and 李世宁 and others}',
        'author_en': 'BAO Hang-Yu, YIN Kang-Lin, CAO Li, LI Shi-Ning, et al.',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'jiatong2020logdiag': {
        'title': '{基于日志数据的分布式软件系统故障诊断综述 [A Survey on Fault Diagnosis of Distributed Software Systems Based on Log Data]}',
        'author': '{贾统 and 李影 and 吴中海}',
        'author_en': 'JIA Tong, LI Ying, WU Zhong-Hai',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'limingshu2019logmgmt': {
        'title': '{大规模分布式系统日志管理技术综述 [A Survey on Log Management Technologies for Large-Scale Distributed Systems]}',
        'author': '{李明树 and 张艳 and 王涛 and 刘俊}',
        'author_en': 'LI Ming-Shu, ZHANG Yan, WANG Tao, LIU Jun',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'liao2016logs': {
        'title': '{大规模软件系统日志研究综述 [A Survey on Logs in Large-Scale Software Systems]}',
        'author': '{廖湘科 and 李姗姗 and 董威 and 贾周阳 and 刘晓东 and 周书林}',
        'author_en': 'LIAO Xiang-Ke, LI Shan-Shan, DONG Wei, JIA Zhou-Yang, LIU Xiao-Dong, ZHOU Shu-Lin',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'yang2020tracingsurvey': {
        'title': '{分布式追踪技术综述 [A Survey on Distributed Tracing Technologies]}',
        'author': '{杨勇 and 李影 and 吴中海}',
        'author_en': 'YANG Yong, LI Ying, WU Zhong-Hai',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'huang2023javatrace': {
        'title': '{面向 Java 微服务系统的透明请求追踪及采样方法 [Transparent Request Tracing and Sampling Method for Java Microservice Systems]}',
        'author': '{黄梓程 and 陈鹏飞 and 余广坝 and 陈泓仰}',
        'author_en': 'HUANG Zi-Cheng, CHEN Peng-Fei, YU Guang-Ba, CHEN Hong-Yang',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'zhang2024servicedep': {
        'title': '{微服务系统服务依赖发现技术综述 [A Survey on Service Dependency Discovery Technologies in Microservice Systems]}',
        'author': '{张齐勋 and 吴一凡 and 杨勇 and 贾统 and 李影 and 吴中海}',
        'author_en': 'ZHANG Qi-Xun, WU Yi-Fan, YANG Yong, JIA Tong, LI Ying, WU Zhong-Hai',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'yuqingyang2022trace': {
        'title': '{基于调用链控制流分析的大型微服务系统性能建模与异常定位 [Performance Modeling and Anomaly Localization for Large-Scale Microservice Systems Based on Call Chain Control Flow Analysis]}',
        'author': '{于庆洋 and 白晓颖 and 李明杰 and 李奇原 and 刘涛 and 刘泽胤 and 裴丹}',
        'author_en': 'YU Qing-Yang, BAI Xiao-Ying, LI Ming-Jie, LI Qi-Yuan, LIU Tao, LIU Ze-Yin, PEI Dan',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'wang2017tracefault': {
        'title': '{一种基于执行轨迹监测的微服务故障诊断方法 [A Microservice Fault Diagnosis Method Based on Execution Trace Monitoring]}',
        'author': '{王智宇 and 王涛 and 张文博 and 陈宁江 and 左春}',
        'author_en': 'WANG Zhi-Yu, WANG Tao, ZHANG Wen-Bo, CHEN Ning-Jiang, ZUO Chun',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'you2021tracelogstorage': {
        'title': '{一种监控系统的链路跟踪型日志数据的存储设计 [A Storage Design of Link-Tracing Log Data for Monitoring Systems]}',
        'author': '{尤勇 and 汪浩 and 任天 and 顾胜晖 and 孙佳林}',
        'author_en': 'YOU Yong, WANG Hao, REN Tian, GU Sheng-Hui, SUN Jia-Lin',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'ding2020decomposition': {
        'title': '{场景驱动且自底向上的单体系统微服务拆分方法 [Scenario-Driven and Bottom-Up Microservice Decomposition Method for Monolithic Systems]}',
        'author': '{丁丹 and 彭鑫 and 郭晓峰 and 张健 and 吴毅坚}',
        'author_en': 'DING Dan, PENG Xin, GUO Xiao-Feng, ZHANG Jian, WU Yi-Jian',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'jia2021loggingdecision': {
        'title': '{基于程序层次树的日志打印位置决策方法 [Logging Position Decision Method Based on Program Hierarchical Tree]}',
        'author': '{贾统 and 李影 and 张齐勋 and 吴中海}',
        'author_en': 'JIA Tong, LI Ying, ZHANG Qi-Xun, WU Zhong-Hai',
        'journal': '{软件学报 [Journal of Software]}'
    },
    'feng2020microservice': {
        'title': '{微服务技术发展的现状与展望 [Current Status and Prospects of Microservice Technology Development]}',
        'author': '{冯志勇 and 徐砚伟 and 薛霄 and 陈世展}',
        'author_en': 'FENG Zhi-Yong, XU Yan-Wei, XUE Xiao, CHEN Shi-Zhan',
        'journal': '{计算机研究与发展 [Journal of Computer Research and Development]}'
    },
    'wuhuayao2020microdev': {
        'title': '{面向微服务软件开发方法研究进展 [Research Progress on Microservice-Oriented Software Development Methods]}',
        'author': '{吴化尧 and 邓文俊}',
        'author_en': 'WU Hua-Yao, DENG Wen-Jun',
        'journal': '{计算机研究与发展 [Journal of Computer Research and Development]}'
    },
    'wei2023cloudlogstorage': {
        'title': '{数据模式感知的低成本云日志存储系统 [Data Schema-Aware Low-Cost Cloud Log Storage System]}',
        'author': '{魏钧宇 and 张广艳 and 陈军超}',
        'author_en': 'WEI Jun-Yu, ZHANG Guang-Yan, CHEN Jun-Chao',
        'journal': '{计算机研究与发展 [Journal of Computer Research and Development]}'
    },
    'fang2024microperf': {
        'title': '{一种基于深度学习的微服务性能异常检测方法 [A Deep Learning-Based Microservice Performance Anomaly Detection Method]}',
        'author': '{方浩天 and 李春花 and 王清 and 周可}',
        'author_en': 'FANG Hao-Tian, LI Chun-Hua, WANG Qing, ZHOU Ke',
        'journal': '{计算机研究与发展 [Journal of Computer Research and Development]}'
    },
    'meiyudong2020logcnn': {
        'title': '{一种基于日志信息和 {CNN-text} 的软件系统异常检测方法 [A Software System Anomaly Detection Method Based on Log Information and {CNN-text}]}',
        'author': '{梅御东 and 陈旭 and 孙毓忠 and others}',
        'author_en': 'MEI Yu-Dong, CHEN Xu, SUN Yu-Zhong, et al.',
        'journal': '{计算机学报 [Chinese Journal of Computers]}'
    },
    'wanglu2023microfault': {
        'title': '{微服务故障检测研究综述 [A Survey on Microservice Fault Detection]}',
        'author': '{王璐 and 姜宇轩 and 李青山 and 霍其恩 and 王展 and 谢生龙 and 歹杰}',
        'author_en': 'WANG Lu, JIANG Yu-Xuan, LI Qing-Shan, HUO Qi-En, WANG Zhan, XIE Sheng-Long, DAI Jie',
        'journal': '{计算机学报 [Chinese Journal of Computers]}'
    },
    'zhou2023fusionad': {
        'title': '{基于融合学习的无监督多维时间序列异常检测 [Unsupervised Multivariate Time Series Anomaly Detection Based on Fusion Learning]}',
        'author': '{周小晖 and 王意洁 and 徐鸿祚 and 刘铭宇}',
        'author_en': 'ZHOU Xiao-Hui, WANG Yi-Jie, XU Hong-Zuo, LIU Ming-Yu',
        'journal': '{计算机研究与发展 [Journal of Computer Research and Development]}'
    },
    'chen2020loganomaly': {
        'title': '{面向云数据中心多语法日志通用异常检测机制 [A Universal Anomaly Detection Mechanism for Multi-Syntax Logs in Cloud Data Centers]}',
        'author': '{陈彦宁 and 张广艳 and 陈康}',
        'author_en': 'CHEN Yan-Ning, ZHANG Guang-Yan, CHEN Kang',
        'journal': '{计算机研究与发展 [Journal of Computer Research and Development]}'
    },
    'liu2017microcontainer': {
        'title': '{面向微服务架构的容器级弹性资源供给方法 [Container-Level Elastic Resource Provisioning Method for Microservice Architecture]}',
        'author': '{刘敏 and 周傲英}',
        'author_en': 'LIU Min, ZHOU Ao-Ying',
        'journal': '{计算机研究与发展 [Journal of Computer Research and Development]}'
    }
}

for key, data in updates.items():
    # Replace title
    content = re.sub(
        rf'(@[a-zA-Z]+\s*\{{\s*{key}\s*,[\s\S]*?)title\s*=\s*\{{[^\}}]+\}}',
        lambda m: f"{m.group(1)}title   = {data['title']}",
        content
    )
    # Replace journal
    content = re.sub(
        rf'(@[a-zA-Z]+\s*\{{\s*{key}\s*,[\s\S]*?)journal\s*=\s*\{{[^\}}]+\}}',
        lambda m: f"{m.group(1)}journal = {data['journal']}",
        content
    )
    # Add English name comment under author if not exists
    content = re.sub(
        rf'(@[a-zA-Z]+\s*\{{\s*{key}\s*,[\s\S]*?author\s*=\s*\{{[^\}}]+\}})(?!\s*%\s*英文对照姓名)',
        lambda m: f"{m.group(1)},\n  % 英文对照姓名：{data['author_en']}",
        content
    )

with open('latex/references.bib', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated references.bib successfully!")
