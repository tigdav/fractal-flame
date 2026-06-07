import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

from flame import mp_runner
from flame.config import AffineParams, Config, FunctionConfig, SizeConfig


def _make_base_config(workers: int = 1) -> Config:
    return Config(
        size=SizeConfig(width=4, height=4),
        iteration_count=10,
        output_path="result.png",
        workers=workers,
        seed=1.0,
        functions=[FunctionConfig(name="swirl", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=1,
    )


def test_split_iterations_even():
    chunks = mp_runner._split_iterations(total=100, workers=4)
    assert chunks == [25, 25, 25, 25]


def test_split_iterations_with_remainder():
    chunks = mp_runner._split_iterations(total=10, workers=3)
    # first workers get +1 until remainder is exhausted
    assert chunks == [4, 3, 3]


def test_split_iterations_when_workers_more_than_iterations():
    chunks = mp_runner._split_iterations(total=3, workers=5)
    assert chunks == [1, 1, 1, 0, 0]


def test_build_worker_config_overrides_iterations_and_seed():
    base = _make_base_config(workers=4)
    worker = mp_runner._build_worker_config(base, iterations=123, seed_offset=2)

    assert isinstance(worker, Config)
    assert worker.iteration_count == 123
    assert worker.seed == pytest.approx(base.seed + 2.0)
    assert worker.workers == 1

    # shared fields are copied as is
    assert worker.size is base.size
    assert worker.output_path == base.output_path
    assert worker.functions is base.functions
    assert worker.affine_params is base.affine_params
    assert worker.gamma_correction is base.gamma_correction
    assert worker.gamma == base.gamma
    assert worker.symmetry_level == base.symmetry_level


def test_generate_flame_single_process_uses_core_function(monkeypatch):
    config = _make_base_config(workers=1)

    fake_hist = np.ones((2, 2), dtype=np.float64)
    fake_colors = np.full((2, 2, 3), 0.5, dtype=np.float64)

    called = {}

    def fake_generate_single(cfg):
        called["cfg"] = cfg
        return fake_hist, fake_colors

    monkeypatch.setattr(mp_runner, "generate_flame_single", fake_generate_single)

    hist, colors = mp_runner.generate_flame(config)

    assert called["cfg"] is config
    assert hist is fake_hist
    assert colors is fake_colors


def test_generate_flame_multi_process_aggregates_worker_results(monkeypatch):
    config = _make_base_config(workers=2)
    config.iteration_count = 10

    def fake_worker_task(cfg):
        shape = (3, 4)
        hist = np.ones(shape, dtype=np.float64)
        idx = int(round(cfg.seed - config.seed))

        if idx == 0:
            colors = np.zeros((*shape, 3), dtype=np.float64)
        else:
            colors = np.ones((*shape, 3), dtype=np.float64)
        return hist, colors

    class FakePool:
        def __init__(self, processes: int):
            self.processes = processes

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def map(self, func, args):
            return [func(a) for a in args]

    monkeypatch.setattr(mp_runner, "_worker_task", fake_worker_task)
    monkeypatch.setattr(mp_runner, "Pool", FakePool)

    hist, colors = mp_runner.generate_flame(config)

    assert hist.shape == (3, 4)
    assert colors.shape == (3, 4, 3)

    # each pixel got hit twice (two workers with hist=1)
    assert np.all(hist == 2.0)

    # first worker contributed color 0.0, second worker color 1.0 -> average is 0.5
    assert np.allclose(colors, 0.5)


@pytest.mark.slow
def test_generate_flame_parallel_faster_than_sequential(monkeypatch):
    """Benchmark-style check: parallel execution finishes faster than
    the naive sequential total (N × sleep_per_worker).

    This is not a performance test — only a correctness check that
    mp_runner splits work and executes tasks concurrently.
    """
    sleep_per_worker = 0.05
    workers = 4

    config = _make_base_config(workers=workers)
    config.iteration_count = 100

    # Fake single-worker compute: blocks for sleep_per_worker.
    def fake_generate_single(cfg):
        time.sleep(sleep_per_worker)
        shape = (cfg.size.height, cfg.size.width)
        hist = np.ones(shape, dtype=np.float64)
        colors = np.zeros((*shape, 3), dtype=np.float64)
        return hist, colors

    monkeypatch.setattr(mp_runner, "generate_flame_single", fake_generate_single)

    # Use a thread pool to simulate parallel workers.
    class ThreadPool:
        def __init__(self, processes: int):
            self._executor = ThreadPoolExecutor(max_workers=processes)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self._executor.shutdown(wait=True)

        def map(self, func, args):
            futures = [self._executor.submit(func, a) for a in args]
            return [f.result() for f in futures]

    monkeypatch.setattr(mp_runner, "Pool", ThreadPool)

    start = time.perf_counter()
    hist, colors = mp_runner.generate_flame(config)
    elapsed = time.perf_counter() - start

    # Basic sanity checks.
    assert hist.shape == (config.size.height, config.size.width)
    assert colors.shape == (config.size.height, config.size.width, 3)

    # If executed sequentially, total time = N × sleep.
    sequential_time = sleep_per_worker * workers

    # Parallel execution must be strictly faster than sequential.
    assert elapsed < sequential_time
