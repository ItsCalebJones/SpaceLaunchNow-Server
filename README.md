[![discord](https://discordapp.com/api/guilds/380226438584074242/embed.png?style=shield)](https://discord.gg/WVfzEDW) [![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=102)](https://github.com/ellerbrock/open-source-badge/) [![Semver](http://img.shields.io/SemVer/3.2.0.png)](http://semver.org/spec/v2.0.0.html)

# SpaceLaunchNow Server
A Django-based Twitter bot, REST API endpoint, and website for [Space Launch Now]().

## Installation

### Get Django and the Frontend Running
Suggest using a Linux or MacOS device however can be ran with Windows.

1. Download/Extract and navigate to the correct directory.
2. (Optional) Create a python [virtual environment](https://virtualenv.pypa.io/en/stable/installation/) for this project.
2. Run: `$ pip install -r requirements.txt` to install required Python packages.
3. Create a log directory with `mkdir log` (will soon be unnecessary)
3. Create an empty logfile with `nano log/daily_digest.log`, then save the file and exit (will soon be unnecessary)
3. Create a config file copy with `cp spacelaunchnow/example_config.py spacelaunchnow/config.py`
3. Initiate the DB with `python manage.py migrate`
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


## Authors

* **Caleb Jones**           - *Initial work*    - [ItsCalebJones](https://github.com/ItsCalebJones)
* **Jacques Rascagneres**   - *Contributer*     - [JRascagneres](https://github.com/JRascagneres)

See also the list of [contributors](https://github.com/itscalebjones/SpaceLaunchNow-Server/contributors) who participated in this project.

## License

This project is licensed under the Apache License - see the [LICENSE](LICENSE.md) file for details

## Acknowledgments

* The wonderful devs and librarians over at [Launch Library](https://launchlibrary.net/)
