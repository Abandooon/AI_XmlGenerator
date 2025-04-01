# src/ablation/runner.py
def run_ablation(config_path):
    config = load_config(config_path)
    # 动态加载模块
    generator = ConstrainedGenerator(enabled=config['use_constraint'])
    validator = ValidatorPipeline(config['validation'])

    for case in test_cases:
        xml = generator.generate(case.req)
        report = validator.validate(xml)
        log_results(report)