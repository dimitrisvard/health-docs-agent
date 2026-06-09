from retrieval.fusion import reciprocal_rank_fusion


def test_rrf_rewards_agreement():
    dense = ["a", "b", "c"]
    lexical = ["b", "a", "d"]
    scores = reciprocal_rank_fusion([dense, lexical])
    # 'a' and 'b' rank high in both lists -> beat single-list 'c' / 'd'
    assert scores["b"] > scores["c"]
    assert scores["a"] > scores["d"]


def test_rrf_empty():
    assert reciprocal_rank_fusion([]) == {}
