import pytest
import yaml
from src.data.loader import load_config, load_words


def test_load_config_success(tmp_path):
    config_data = {"key": "value", "number": 123}
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = load_config(config_file)
    assert config == config_data


def test_load_config_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_config.yaml")


def test_load_words_success(tmp_path):
    csv_content = "id,word\n1,hello\n2,world"
    csv_file = tmp_path / "words.csv"
    with open(csv_file, "w") as f:
        f.write(csv_content)

    words = load_words(csv_file)
    assert words == {0: "hello", 1: "world"}
    assert len(words) == 2


def test_load_words_not_found():
    with pytest.raises(FileNotFoundError):
        load_words("non_existent_words.csv")
