# TODO List

37. 查找所有类型的的swc及其最小模型（minoccurs=1），转为schema\gbnf\fsm
38. 处理pdf、自然语言转为结构化输入的模块
39. 开发网页端交互界面
40. 第一轮对话输出也要限定schema
41. 


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






