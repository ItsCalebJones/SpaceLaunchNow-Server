import toml


def read_package_name_from_pyproject(file_path="pyproject.toml"):
    # Load the pyproject.toml file
    with open(file_path) as file:
        pyproject_content = toml.load(file)

    # Access the name from the `[tool.poetry]` section
    name = pyproject_content["tool"]["poetry"]["name"]
    return name


def read_version_from_pyproject(file_path="pyproject.toml"):
    # Load the pyproject.toml file
    with open(file_path) as file:
        pyproject_content = toml.load(file)

    # Access the version from the `[tool.poetry]` section
    version = pyproject_content["tool"]["poetry"]["version"]
    return version
