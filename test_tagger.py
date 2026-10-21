from tagger import classify

BAE_DESC = ("Location: UK Flex - Christchurch/Yeovil. We offer a range of hybrid and flexible working "
            "arrangements, however for this role you will be expected to attend your site 3-5 days per week.")


def test_bae_example():
    t = classify("Graduate Digital Intelligence Network Engineer (Group DI)", BAE_DESC, 2028)
    assert t.kind == "graduate" and t.network_relevant
    assert t.work_pattern == "hybrid"
    assert t.fit == "check"  # no year stated


def test_meta_example():
    t = classify("Network Production Engineer (University Grad) Meta", "", 2028)
    assert t.kind == "graduate" and t.network_relevant and t.fit == "check"


def test_year_logic():
    assert classify("Graduate Network Engineer 2028 intake", "", 2028).fit == "match"
    assert classify("Graduate Network Engineer 2027 intake", "", 2028).fit == "too_early"
    assert classify("Graduate Network Engineer 2029 intake", "", 2028).fit == "too_late"


def test_placement_before_graduating():
    t = classify("Network Engineering Industrial Placement 2027", "", 2028)
    assert t.kind == "placement" and t.fit == "match"


def test_senior_and_irrelevant_filtered():
    assert classify("Senior Network Engineer", "5+ years experience", 2028).fit == "not_relevant"
    assert classify("Graduate Marketing Executive", "", 2028).fit == "not_relevant"


def test_clearance_flag():
    t = classify("Graduate Network Engineer", "Must be eligible for SC security clearance", 2028)
    assert t.clearance_or_nationality
