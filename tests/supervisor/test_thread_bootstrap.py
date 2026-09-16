from dataclasses import dataclass

from popp_supervisor.thread_bootstrap import ensure_thread_dataset


@dataclass
class Result:
    stdout: str = "Done\n"
    stderr: str = ""
    returncode: int = 0


class FakeRunner:
    def __init__(self, active_output: str):
        self.active_output = active_output
        self.calls: list[list[str]] = []

    def __call__(self, args, **kwargs):
        self.calls.append(list(args))
        if args[1:] == ["dataset", "active", "-x"]:
            return Result(stdout=self.active_output)
        return Result()


def test_existing_active_dataset_is_never_mutated():
    runner = FakeRunner("aa" * 64 + "\nDone\n")
    result = ensure_thread_dataset("/opt/popp/bin/ot-ctl", 20, runner=runner)
    assert result.state == "existing"
    assert runner.calls == [
        ["/opt/popp/bin/ot-ctl", "dataset", "active", "-x"],
        ["/opt/popp/bin/ot-ctl", "ifconfig", "up"],
        ["/opt/popp/bin/ot-ctl", "thread", "start"],
    ]
    assert not any("init" in call or "commit" in call or "channel" in call for call in runner.calls)

def test_blank_otbr_forms_network_on_shared_channel():
    runner = FakeRunner("Error 23: NotFound\n")
    result = ensure_thread_dataset("/opt/popp/bin/ot-ctl", 20, runner=runner)
    assert result.state == "created"
    assert runner.calls == [
        ["/opt/popp/bin/ot-ctl", "dataset", "active", "-x"],
        ["/opt/popp/bin/ot-ctl", "dataset", "init", "new"],
        ["/opt/popp/bin/ot-ctl", "dataset", "channel", "20"],
        ["/opt/popp/bin/ot-ctl", "dataset", "commit", "active"],
        ["/opt/popp/bin/ot-ctl", "ifconfig", "up"],
        ["/opt/popp/bin/ot-ctl", "thread", "start"],
    ]


def test_empty_done_output_is_treated_as_no_dataset():
    runner = FakeRunner("Done\n")
    result = ensure_thread_dataset("ot-ctl", 15, runner=runner)
    assert result.state == "created"


def test_invalid_channel_is_rejected_before_touching_radio():
    runner = FakeRunner("Done\n")
    try:
        ensure_thread_dataset("ot-ctl", 27, runner=runner)
    except ValueError as err:
        assert "11..26" in str(err)
    else:
        raise AssertionError("expected ValueError")
    assert runner.calls == []