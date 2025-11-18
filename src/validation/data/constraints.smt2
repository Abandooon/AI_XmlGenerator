; AUTOSAR Validation Constraints Template
; 包含单文件和跨文件约束

(set-logic ALL)

; ========== Sort Declarations ==========
(declare-sort APPLICATION-SW-COMPONENT-TYPE 0)
(declare-sort COMPOSITION-SW-COMPONENT-TYPE 0)
(declare-sort SW-COMPONENT-PROTOTYPE 0)
(declare-sort R-PORT-PROTOTYPE 0)
(declare-sort P-PORT-PROTOTYPE 0)
(declare-sort SENDER-RECEIVER-INTERFACE 0)
(declare-sort APPLICATION-PRIMITIVE-DATA-TYPE 0)
(declare-sort VARIABLE-DATA-PROTOTYPE 0)
(declare-sort COMPU-METHOD 0)
(declare-sort PORTS-Container 0)

; ========== Function Declarations ==========

; 单文件约束 - 元素属性存在性
(declare-fun has_shortName (APPLICATION-SW-COMPONENT-TYPE) Bool)
(declare-fun has_shortName (P-PORT-PROTOTYPE) Bool)
(declare-fun has_shortName (R-PORT-PROTOTYPE) Bool)
(declare-fun has_shortName (SENDER-RECEIVER-INTERFACE) Bool)

(declare-fun has_ports (APPLICATION-SW-COMPONENT-TYPE) Bool)
(declare-fun has_category (APPLICATION-PRIMITIVE-DATA-TYPE) Bool)

; 跨文件约束 - 引用解析
(declare-fun ref_target_exists (String) Bool)
(declare-fun ref_type_matches (String String) Bool)

(declare-fun port_has_interface_ref (R-PORT-PROTOTYPE) Bool)
(declare-fun port_has_interface_ref (P-PORT-PROTOTYPE) Bool)

(declare-fun has_typeRef (VARIABLE-DATA-PROTOTYPE) Bool)
(declare-fun typeRef_resolves (VARIABLE-DATA-PROTOTYPE) Bool)

; ========== Single-File Constraints ==========

; 约束S1: 组件必须有SHORT-NAME
(assert
  (forall ((comp APPLICATION-SW-COMPONENT-TYPE))
    (has_shortName comp)))

; 约束S2: 组件必须有PORTS容器
(assert
  (forall ((comp APPLICATION-SW-COMPONENT-TYPE))
    (has_ports comp)))

; 约束S3: P端口必须有SHORT-NAME
(assert
  (forall ((port P-PORT-PROTOTYPE))
    (has_shortName port)))

; 约束S4: R端口必须有SHORT-NAME
(assert
  (forall ((port R-PORT-PROTOTYPE))
    (has_shortName port)))

; 约束S5: 接口必须有SHORT-NAME
(assert
  (forall ((iface SENDER-RECEIVER-INTERFACE))
    (has_shortName iface)))

; ========== Cross-File Constraints ==========

; 约束C1: 所有端口的接口引用必须解析到存在的接口
(assert
  (forall ((path String))
    (=> (ref_target_exists path)
        true)))

; 约束C2: 引用的DEST类型必须与实际目标类型匹配
(assert
  (forall ((path String) (expected_type String))
    (=> (ref_target_exists path)
        (ref_type_matches path expected_type))))

; 约束C3: 数据元素的TYPE-TREF必须解析到有效的数据类型
(assert
  (forall ((dataElem VARIABLE-DATA-PROTOTYPE))
    (=> (has_typeRef dataElem)
        (typeRef_resolves dataElem))))

; 不要写 (check-sat)，验证器会自动添加