import textwrap

from social_agent.config import AgentConfig, WordPressConfig, load_config


def test_wordpress_feed_url_combines_site_and_path():
    config = WordPressConfig(site_url="https://yenifikirler.org", feed_path="/atom")
    assert config.feed_url == "https://yenifikirler.org/atom"


def test_load_config_expands_environment_variables(tmp_path, monkeypatch):
    config_path = tmp_path / "agent.config.yaml"
    state_file = tmp_path / "state.json"
    monkeypatch.setenv("TEST_SITE_URL", "https://yenifikirler.org")
    monkeypatch.setenv("TEST_STATE_FILE", str(state_file))
    config_path.write_text(
        textwrap.dedent(
            """
            wordpress:
              site_url: ${TEST_SITE_URL}
              poll_interval: 120
            state_file: ${TEST_STATE_FILE}
            """
        ).strip()
    )

    config = load_config(config_path)

    assert isinstance(config, AgentConfig)
    assert config.wordpress.feed_url == "https://yenifikirler.org/feed"
    assert config.state_file == state_file.resolve()
