# SpaceLaunchNow Server
A Django-based Twitter bot, REST API endpoint, and website for [Space Launch Now]().

## Installation

### Get Django and the Frontend Running
Suggest using a Linux or MacOS device however can be ran with Windows.

1. Download/Extract and navigate to the correct directory.
2. (Optional) Create a python [virtual environment](https://virtualenv.pypa.io/en/stable/installation/) for this project.
2. Run: `$ pip install -r requirements.txt` to install required Python packages.
3. Initiate the DB with `python manage.py runmigrations`
4. Run the server - `python manage.py runserver`
5. Open a browser and navigate to 127.0.0.1:8000

### Twitter Bot - (Advanced: Requires ActiveMQ and Django-Celery)
TODO - Fill this out.


## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## Versioning

We use [SemVer](http://semver.org/) for versioning.

### Summary

Given a version number MAJOR.MINOR.PATCH, increment the:

* MAJOR version when you make incompatible API changes,
* MINOR version when you add functionality in a backwards-compatible manner, and
* PATCH version when you make backwards-compatible bug fixes.
Additional labels for pre-release and build metadata are available as extensions to the MAJOR.MINOR.PATCH format.

## Authors

* **Caleb Jones**           - *Initial work*    - [ItsCalebJones](https://github.com/ItsCalebJones)
* **Jacques Rascagneres**   - *Contributer*     - [JRascagneres](https://github.com/JRascagneres)

See also the list of [contributors](https://github.com/itscalebjones/SpaceLaunchNow-Server/contributors) who participated in this project.

## License

This project is licensed under the Apache License - see the [LICENSE](LICENSE.md) file for details

## Acknowledgments

* The wonderful devs and librarians over at [Launch Library](https://launchlibrary.net/)
