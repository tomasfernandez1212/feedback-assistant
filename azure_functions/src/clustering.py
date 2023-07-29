from hdbscan import HDBSCAN  # type: ignore

from typing import List


def cluster_embeddings(
    embeddings: List[List[float]], min_cluster_size: int = 5
) -> List[int]:
    """
    Cluster embeddings using HDBSCAN.
    :param embeddings: List of embeddings, where each embedding is a list of floats.
    :param min_cluster_size: Minimum number of points in a cluster.
    :return: List of cluster labels, where each label is an integer.
    """
    clusterer = HDBSCAN(min_cluster_size=min_cluster_size, gen_min_span_tree=True)
    cluster_labels = clusterer.fit_predict(embeddings)  # type: ignore
    return cluster_labels  # type: ignore
