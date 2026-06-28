from examples.agent_loops.repair_loop_demo import main as repair_main
from examples.agent_loops.verify_before_final_answer import main as verify_main


def test_agent_loop_examples_run(capsys):
    verify_main()
    repair_main()

    captured = capsys.readouterr()
    assert "推荐" in captured.out or "recommend" in captured.out.lower()
    assert "SonicLite AirBuds" in captured.out
