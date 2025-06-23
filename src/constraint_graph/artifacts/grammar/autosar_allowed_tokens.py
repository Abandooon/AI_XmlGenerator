    """autosar_allowed_tokens – AUTO-GENERATED
    ------------------------------------------------
    • FSM file : autosar.fsm
    • Compress : True
    • On-demand: True
    """
    from __future__ import annotations
    import functools
    from typing import List, Optional

    _ROOT_DFA = {}
    _GRAMMAR = (
"start : dummy_root\ndummy_root : \"DUMMY\"\ncid_9586_list : \"SwComponentPrototypes\" | \"SwConnectors\" | \"Chapters\" | \"of\" | \"SwComponentDocumentation:\" | \"PostBuild\" | \"binding\" | \"Existence\" | \"of\" | \"PortPrototypes:\" | \"preCompileTime\" | \"latestBindingTime\"\ncid_9588_list : \"preCompileTime\"\ncid_9590_list : \"preCompileTime\"\ncid_9640_list : \"anyStandardized\"\ncid_9666_list : \"in\" | \"out\" | \"inout\"\ncid_9679_list : \"1..63\" | \"or\" | \"0\" | \"if\" | \"representing\" | \"E_OK\"\ncid_9686_list : \"STANDARD\" | \"QUEUED\"\ncid_9690_list : \"notAccessible\" | \"readOnly\"\ncid_9737_list : \"not\" | \"queued\"\ncid_9738_list : \"queued\"\ncid_9740_list : \"not\" | \"queued\"\ncid_9741_list : \"queued\"\ncid_9745_list : \"false\"\ncid_9821_list : \"MODE_MANAGEMENT\" | \"PARTIAL_NETWORKING\"\ncid_9830_list : \"NONE\" | \"PROFILE_01\" | \"PROFILE_02\"\ncid_9836_list : \"Cardinality:\" | \"1\" | \"Range:\" | \"[0\" | \"..\" | \"65535]\"\ncid_9837_list : \"[0\" | \"..\" | \"3]\"\ncid_9838_list : \"Range:\" | \"[0\" | \"..\" | \"65535]\" | \"value\" | \"mod\" | \"4\" | \"=\" | \"0\"\ncid_9839_list : \"Range:\" | \"[0\" | \"..\" | \"65535]\" | \"value\" | \"mod\" | \"4\" | \"=\" | \"0\"\ncid_9840_list : \"Range:\" | \"[0\" | \"..\" | \"240]\" | \"value\" | \"mod\" | \"8\" | \"=\" | \"0\"\ncid_9841_list : \"[0\" | \"..\" | \"14]\"\ncid_9842_list : \"[0\" | \"..\" | \"14]\"\ncid_9843_list : \"[0\" | \"..\" | \"14]\"\ncid_9847_list : \"12\"\ncid_9850_list : \"Range:\" | \"[0\" | \"..\" | \"65535]\" | \"value\" | \"mod\" | \"8\" | \"=\" | \"0\"\ncid_9851_list : \"Cardinality:\" | \"16\" | \"(ordered)\" | \"Range:\" | \"[0\" | \"..\" | \"255]\"\ncid_9852_list : \"[0\" | \"..\" | \"15]\"\ncid_9853_list : \"[0\" | \"..\" | \"15]\"\ncid_9854_list : \"[0\" | \"..\" | \"15]\"\ncid_9860_list : \"PARTIAL_NETWORKING\"\ncid_9866_list : \"the\" | \"ClientServerOperations\" | \"that\" | \"are\" | \"also\" | \"referenced\" | \"by\" | \"the\" | \"OperationInvokedEvents\"\ncid_9871_list : \"LINEAR\" | \"IDENTICAL\" | \"SCALE_LINEAR_AND_TEXTTABLE\" | \"TEXTTABLE\" | \"BITFIELD_TEXTTABLE\"\ncid_9880_list : \"false\"\ncid_9919_list : \"VSA_LINEAR\" | \"VSA_SQUARE\" | \"VSA_RECTANGULAR\" | \"VSA_FULLY_FLEXIBLE\"\ncid_9934_list : \">0\"\ncid_9942_list : \"TYPE_REFERENCE\"\ncid_9951_list : \"TYPE_REFERENCE\" | \"FUNCTION_REFERENCE\" | \"VALUE\"\ncid_9981_list : \"enum\"\ncid_9986_list : \"standard\" | \"queued\" | \"or\" | \"measurementPoint\"\ncid_9987_list : \"standard\"\ncid_9988_list : \"standard\"\ncid_9989_list : \"standard\"\ncid_9990_list : \"standard\"\ncid_9991_list : \"standard\" | \"or\" | \"measurementPoint\"\ncid_9992_list : \"standard\" | \"measurementPoint\" | \"or\" | \"message\"\ncid_9993_list : \"standard\" | \"const\" | \"or\" | \"fixed\"\ncid_9994_list : \"standard\"\ncid_9995_list : \"standard\"\ncid_9996_list : \"standard\"\ncid_9997_list : \"standard\" | \"const\" | \"or\" | \"fixed\"\ncid_9998_list : \"standard\"\ncid_9999_list : \"standard\" | \"or\" | \"const\"\ncid_10000_list : \"standard\"\ncid_10005_list : \"HandleInvalidEnum.dontInvalidate\"\ncid_10013_list : \"the\" | \"applicable\" | \"text\" | \"values\"\ncid_10019_list : \"SwCalibrationAccessEnum.notAccessible\"\ncid_10067_list : \"0\"\ncid_10080_list : \"0\" | \"1\"\ncid_10104_list : \"FILL_UNTIL_END\" | \"FILL_UNTIL_MAX_SIZE\"\ncid_10127_list : \"BITFIELD_TEXTTABLE\" | \"or\" | \"TEXTTABLE\"\ncid_10128_list : \"FIXED_LENGTH\" | \"VARIABLE_LENGTH\"\ncid_10143_list : \"COUNTRY\" | \"CALCULATION\" | \"EQUIV_UNITS\"\ncid_10154_list : \"VALUE\"\ncid_10169_list : \"the\" | \"applicable\" | \"text\" | \"values\"\ncid_10182_list : \"Unit.factorSiToUnit:\" | \"1\" | \"Unit.offsetSiToUnit:\" | \"0\"\ncid_10232_list : \"nfold\"\ncid_10233_list : \"single\"\ncid_10234_list : \"single\"\ncid_10236_list : \"nfold\"\ncid_10285_list : \"0\" | \"..\" | \"31\"\ncid_10290_list : \"0\"\ncid_10292_list : \">\" | \"0\"\ncid_10319_list : \"DATA_REFERENCE\"\ncid_10322_list : \"STANDARD\" | \"QUEUED\"\ncid_10326_list : \"communicationInterEcu\"\ncid_10330_list : \"not\" | \"queued\"\ncid_10336_list : \"not\" | \"queued\"\ncid_10368_list : \"enableTakeAddress=true\" | \"implies\" | \"SwcInternalBehavior.supportsMultipleInstantiation=false\"\ncid_10371_list : \"category\" | \"shall\" | \"be\" | \"VALUE\" | \"or\" | \"TYPE_REFERENCE\" | \"(with\" | \"target\" | \"data\" | \"type\" | \"category\" | \"VALUE)\"\ncid_10471_list : \"DiagEventDebounceCounterBased\" | \"OR\" | \"DiagEventDebounceTimeBased\"\ncid_10473_list : \"DiagEventDebounceMonitorInternal\"\ncid_10513_list : \"requestCallbackTypeManufacturer\"\ncid_10514_list : \"requestCallbackTypeSupplier\"\ncid_10515_list : \"CAT1\" | \"CAT2\" | \"OXS1\" | \"OXS2\" | \"EGR\" | \"SAIR\" | \"EVAP\" | \"SECOXS1\" | \"SECOXS2\" | \"NMHCCAT\" | \"NOXCAT\" | \"NOXADSORB\" | \"PMFILTER\" | \"EGSENSOR\" | \"BOOSTPRS\" | \"NOGROUP\" | \"NONE\"\ncid_10568_list : \"EXPLICIT_ORDER\" | \"ALPHABETIC_ORDER\"\ncid_10573_list : \"ALPHABETIC_ORDER\"\ncid_10618_list : \"true\"\ncid_10626_list : \"true\"\ncid_10637_list : \"RPortPrototypes\" | \"typed\" | \"by\" | \"SenderReceiverInterface\" | \"OR\" | \"PortPrototypes\" | \"typed\" | \"by\" | \"PortInterface\" | \"with\" | \"isService=true\"\ncid_10638_list : \"RPortPrototypes\" | \"typed\" | \"by\" | \"SenderReceiverInterfaces\" | \"in\" | \"a\" | \"1:n\" | \"scenario\"\ncid_10642_list : \"PortPrototypes\" | \"(NvDataInterface\" | \"or\" | \"ClientServerInterface)\" | \"OR\" | \"RPortPrototypes\" | \"(ModeSwitchInterface)\"\ncid_10645_list : \"false\"\ncid_10647_list : \"NvDataPort\"\ncid_10674_list : \"true\"\ncid_10675_list : \"true\"\ncid_10676_list : \"true\"\ncid_10713_list : \"RPT_SYSTEM\"\ncid_10714_list : \"RPT_SYSTEM\""
    )

    from lark import Lark
    _PARSER = Lark(_GRAMMAR, parser='lalr', maybe_placeholders=False)

    _CACHE_SIZE = 10000

    def _calc_follow(prefix_tokens: List[str]) -> List[str]:
        """Lazy follow-set using Lark when not in _ROOT_DFA."""
        return [t.value for t in _PARSER.parse_interactive(' '.join(prefix_tokens)).accepts()]

    @functools.lru_cache(maxsize=_CACHE_SIZE)
    def _allowed(prefix: str) -> Optional[List[int]]:
        toks = prefix.split() if prefix else []
        state = ' '.join(toks)
        if state in _ROOT_DFA:
            # stored subset
            return _ROOT_DFA[state]
        follow = _calc_follow(toks)
        return follow

    # vLLM entry point -------------------------------------------------
    def allowed(prefix_ids, tokenizer) -> Optional[List[int]]:
        """
        Args:
            prefix_ids : list[int] – already emitted *token ids*
            tokenizer  : tokenizer with decode()
        Returns:
            *list[int]* of *token ids* allowed next, or None to disable
        """
        if not prefix_ids or not tokenizer:
            return None  # disable filter for degenerate cases
        prefix_txt = tokenizer.decode(prefix_ids, skip_special_tokens=True).strip()
        follow_terms = _allowed(prefix_txt)
        if follow_terms is None:
            return None
        return [tokenizer.encode(t, add_special_tokens=False)[0] for t in follow_terms]
