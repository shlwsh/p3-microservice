import re

with open('latex/references.bib', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    (r"title   = \{智能运维的实践: 现状与标准化\}", r"title   = {智能运维的实践: 现状与标准化 [Practice of AIOps: Status Quo and Standardization]}"),
    (r"journal = \{软件学报\}", r"journal = {软件学报 [Journal of Software]}"),
    (r"title   = \{基于日志数据的分布式软件系统故障诊断综述\}", r"title   = {基于日志数据的分布式软件系统故障诊断综述 [A Survey on Fault Diagnosis of Distributed Software Systems Based on Log Data]}"),
    (r"title   = \{大规模分布式系统日志管理技术综述\}", r"title   = {大规模分布式系统日志管理技术综述 [A Survey on Log Management Technologies for Large-Scale Distributed Systems]}"),
    (r"title   = \{大规模软件系统日志研究综述\}", r"title   = {大规模软件系统日志研究综述 [A Survey on Logs in Large-Scale Software Systems]}"),
    (r"title   = \{分布式追踪技术综述\}", r"title   = {分布式追踪技术综述 [A Survey on Distributed Tracing Technologies]}"),
    (r"title   = \{面向 Java 微服务系统的透明请求追踪及采样方法\}", r"title   = {面向 Java 微服务系统的透明请求追踪及采样方法 [Transparent Request Tracing and Sampling Method for Java Microservice Systems]}"),
    (r"title   = \{微服务系统服务依赖发现技术综述\}", r"title   = {微服务系统服务依赖发现技术综述 [A Survey on Service Dependency Discovery Technologies in Microservice Systems]}"),
    (r"title   = \{基于调用链控制流分析的大型微服务系统性能建模与异常定位\}", r"title   = {基于调用链控制流分析的大型微服务系统性能建模与异常定位 [Performance Modeling and Anomaly Localization for Large-Scale Microservice Systems Based on Call Chain Control Flow Analysis]}"),
    (r"title   = \{一种基于执行轨迹监测的微服务故障诊断方法\}", r"title   = {一种基于执行轨迹监测的微服务故障诊断方法 [A Microservice Fault Diagnosis Method Based on Execution Trace Monitoring]}"),
    (r"title   = \{一种监控系统的链路跟踪型日志数据的存储设计\}", r"title   = {一种监控系统的链路跟踪型日志数据的存储设计 [A Storage Design of Link-Tracing Log Data for Monitoring Systems]}"),
    (r"title   = \{场景驱动且自底向上的单体系统微服务拆分方法\}", r"title   = {场景驱动且自底向上的单体系统微服务拆分方法 [Scenario-Driven and Bottom-Up Microservice Decomposition Method for Monolithic Systems]}"),
    (r"title   = \{基于程序层次树的日志打印位置决策方法\}", r"title   = {基于程序层次树的日志打印位置决策方法 [Logging Position Decision Method Based on Program Hierarchical Tree]}"),
    (r"title   = \{微服务技术发展的现状与展望\}", r"title   = {微服务技术发展的现状与展望 [Current Status and Prospects of Microservice Technology Development]}"),
    (r"journal = \{计算机研究与发展\}", r"journal = {计算机研究与发展 [Journal of Computer Research and Development]}"),
    (r"title   = \{面向微服务软件开发方法研究进展\}", r"title   = {面向微服务软件开发方法研究进展 [Research Progress on Microservice-Oriented Software Development Methods]}"),
    (r"title   = \{数据模式感知的低成本云日志存储系统\}", r"title   = {数据模式感知的低成本云日志存储系统 [Data Schema-Aware Low-Cost Cloud Log Storage System]}"),
    (r"title   = \{一种基于深度学习的微服务性能异常检测方法\}", r"title   = {一种基于深度学习的微服务性能异常检测方法 [A Deep Learning-Based Microservice Performance Anomaly Detection Method]}"),
    (r"title   = \{一种基于日志信息和 \{CNN-text\} 的软件系统异常检测方法\}", r"title   = {一种基于日志信息和 {CNN-text} 的软件系统异常检测方法 [A Software System Anomaly Detection Method Based on Log Information and {CNN-text}]}"),
    (r"journal = \{计算机学报\}", r"journal = {计算机学报 [Chinese Journal of Computers]}"),
    (r"title   = \{微服务故障检测研究综述\}", r"title   = {微服务故障检测研究综述 [A Survey on Microservice Fault Detection]}"),
    (r"title   = \{基于融合学习的无监督多维时间序列异常检测\}", r"title   = {基于融合学习的无监督多维时间序列异常检测 [Unsupervised Multivariate Time Series Anomaly Detection Based on Fusion Learning]}"),
    (r"title   = \{面向云数据中心多语法日志通用异常检测机制\}", r"title   = {面向云数据中心多语法日志通用异常检测机制 [A Universal Anomaly Detection Mechanism for Multi-Syntax Logs in Cloud Data Centers]}"),
    (r"title   = \{面向微服务架构的容器级弹性资源供给方法\}", r"title   = {面向微服务架构的容器级弹性资源供给方法 [Container-Level Elastic Resource Provisioning Method for Microservice Architecture]}")
]

for old, new in replacements:
    content = re.sub(old, new, content)

with open('latex/references.bib', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated references.bib exactly!")
