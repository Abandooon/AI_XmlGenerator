本模块功能为提取xsd和xmi数据并合并
执行顺序为xmi_parser->xsd_parser->merge
输出为json文件，unified_metadata.json 
主函数为main，串联执行（尚未验证）

xsd解析器设计文档见项目“AUTOSAR模型解析器”