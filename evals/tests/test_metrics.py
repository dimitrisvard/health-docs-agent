from evals.metrics import hit_at_k, mrr, ndcg


def test_hit_at_k():
    assert hit_at_k(["1", "2", "3"], {"3"}, 5) is True
    assert hit_at_k(["1", "2", "3"], {"9"}, 5) is False


def test_mrr():
    assert mrr(["1", "2", "3"], {"2"}) == 0.5
    assert mrr(["1", "2", "3"], {"9"}) == 0.0


def test_ndcg_perfect():
    assert ndcg(["1", "2"], {"1", "2"}, 2) == 1.0
