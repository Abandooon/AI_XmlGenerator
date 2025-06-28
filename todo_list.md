# TODO List

19. 应将etas示例工程和规范文档中的listing(如5.1) 示例arxml提取出来放入知识图谱作为小样本学习样例,6.16.2.1 Legal Use这样的使用实例也应该放入样本-----etas工程通过云端 / API 进行小样本学习
25. 生成报告、辅助配置、代码生成模板都应该看做衍生功能层，代码生成也是基于元模型和文档的，同样是一个不能直接由llm生成的典型领域，可以看一下asw生成的代码——接口c文件，实现好像是rte的。
33. “并不是xml_tag以tref结尾，你了解autosar的标签吗？引用类型以-REF -TREF -IREF结尾，比如：raw_attributes: {"classId": 1004, "attrId": 2037, 
"xml_tag": "START-ON-EVENT-REF", "xml_wrapper_tag": null, "isXmlAttr": false, "minOccurs": 0, "maxOccurs": 1, "typeId": 4099, 
"attributeClass": false, "allowedValues": null}对应类raw_classes: {"classId": 4099, "className": "StartOnEventRef", 
"xml_tag": null, "xml_wrapper_tag": null}（注意这种类没有xml_tag，所以要由id判断），而{"classId": 4099, "attrId": 4100, "xml_tag": "DEST", 
"xml_wrapper_tag": null, "isXmlAttr": true, "minOccurs": null, "maxOccurs": null, "typeId": 8400, "attributeClass": false, 
"allowedValues": null}是这个类的属性，同时有raw_enums: {"enumId": 8400, "values": ["RUNNABLE-ENTITY"]}。
并且他的父类ref中有个"isAttribute": true的类，即有value值但是不受约束。最终的xml结构就为：
<START-ON-EVENT-REF DEST="RUNNABLE-ENTITY">/COM_SWC/ASW_COM/SwcInternalBehavior/RE_COM_SWC</START-ON-EVENT-REF>这样的形式，
分析逻辑并给出需要修改的代码”
34. 


可能存在问题：
3. 需要对***Ref单独说明吗--------构建知识图谱和生成xml时需要

注：
1. llm提取结构化约束可能适用于标准文档中提取元模型，可能可以推广到其他没有直接定义元模型的标准领域，可以尝试，成功将适用更多领域（标准作业程序 (SOPs)）
2. AuraSAR (奥拉SAR/灵晖SAR):Aura (光环，氛围，也指微妙的预示或智慧的氛围) + SAR 含义：为AUTOSAR配置带来清晰洞察和智能光环的助手。
3. 思考：考虑到最大输出token的限制，应该多阶段生成一个完整的项目，模仿人类工程师配置过程，后续实例引用先前示例，考虑basex查找引用放入上下文中.
4. ASW只生成arxml，代码生成主要由RTE实现（辅助系统）

变体:-------->在上下文注入和元模型链接里改
case1:类->类conditional->类content(在complextype中聚合)------>因此针对这种情况需要提到group中
case2: 属性aggr/attr/iref----->不需要更改
case3: 属性Ref->类中多一个变体点和属性类型为xxxRefConditional，该类同样有变体点属性，
但是该类的qualifiedName与引用类型xxx重名了（当前会覆盖掉原来的这个类），比如PortPrototypeRefConditional
xxxConditional都有是由变体生成的的说明

记录一处异构元模型不一致的地方，ASW文档、uml模型中ApplicationCompositeElementInPortInterfaceInstanceRef类存在base属性，而xsd没有----constr_1184
属性 'swCalprmAxisTypeProps' 在元数据类 'SwCalprmAxis没有----TPS_SWCT_01504






