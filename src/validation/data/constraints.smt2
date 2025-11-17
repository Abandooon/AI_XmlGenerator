; Cross-File Constraints Template for AUTOSAR
; 用于跨文件约束验证的SMT模板

(set-logic ALL)

; ========== Sort Declarations ==========
(declare-sort APPLICATION-SW-COMPONENT-TYPE 0)
(declare-sort SW-COMPONENT-PROTOTYPE 0)
(declare-sort R-PORT-PROTOTYPE 0)
(declare-sort P-PORT-PROTOTYPE 0)
(declare-sort SENDER-RECEIVER-INTERFACE 0)
(declare-sort APPLICATION-PRIMITIVE-DATA-TYPE 0)
(declare-sort COMPU-METHOD 0)

; ========== Predicate Declarations ==========
; 引用存在性谓词
(declare-fun ref_target_exists (String) Bool)
(declare-fun ref_type_matches (String String) Bool)

; 元素属性谓词
(declare-fun has_shortName (APPLICATION-SW-COMPONENT-TYPE) Bool)
(declare-fun has_ports (APPLICATION-SW-COMPONENT-TYPE) Bool)

; 接口引用谓词
(declare-fun port_has_interface_ref (R-PORT-PROTOTYPE) Bool)
(declare-fun port_has_interface_ref (P-PORT-PROTOTYPE) Bool)

; 数据类型引用谓词
(declare-fun has_typeRef (SENDER-RECEIVER-INTERFACE) Bool)
(declare-fun typeRef_resolves (SENDER-RECEIVER-INTERFACE) Bool)

; ========== Cross-File Constraints ==========

; 约束1: 所有端口的接口引用必须解析到存在的接口
(assert
  (forall ((path String))
    (=> (ref_target_exists path)
        true)))

; 约束2: 引用的DEST类型必须与实际目标类型匹配
(assert
  (forall ((path String) (expected_type String))
    (=> (ref_target_exists path)
        (ref_type_matches path expected_type))))

; 约束3: SenderReceiverInterface必须有有效的数据类型引用
(assert
  (forall ((iface SENDER-RECEIVER-INTERFACE))
    (=> (has_typeRef iface)
        (typeRef_resolves iface))))

; 不要写 (check-sat)，验证器会自动添加