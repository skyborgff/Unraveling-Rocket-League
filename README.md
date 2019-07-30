# Unraveling Rocket League

Unraveling Rocket League is a series that tries to discover the underlying physics that rule the video game Rocket League.

Join me over at RLBot Discord channel

[<img src="https://img.shields.io/discord/348658686962696195.svg?colorB=7581dc&logo=discord&logoColor=white">](https://discord.gg/zbaAKPt)

The serie can be followed on [Twitch](https://www.twitch.tv/skyborg), and in the future, on [Youtube](https://www.youtube.com/channel/UCiGBLPMDeDBfALHbJkfQeIg).

This project uses the [RLBot Framework](http://www.rlbot.org/) to control a custom bot that logs the data.

[<img src="https://img.shields.io/pypi/v/rlbot.svg">](https://pypi.org/project/rlbot/)

![Throttle Data](https://i.gyazo.com/e94099da6e38f32c483db8fdb325052c.gif)

### Requirements

- Python 3.7
- Rocket League

## Installation

- Update Rocket League to the latest version
- Clone this repository

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install numpy and pyqtraph.

```bash
pip install numpy
pip install pyqtgraph
pip install PyOpenGL PyOpenGL_accelerate
```

If the later resulted in an error, try this

```bash
pip install PyOpenGL-accelerate==3.1.3b1
```

## Usage

### Gather Data

- Change rlbot.cfg to point to the right files bot configuration. By default it will point to the throttle data gatherer.
- Run `run.bat`
This will start Rocket League and gather all the data 

### Visualize Data

Open `cmd` in one of the analisis folders.
```bash
python visualizer.py 
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)