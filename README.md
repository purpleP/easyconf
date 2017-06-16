This projects simplifies working with configs.
You give it jsonschema of you config and after that you can specify some parts of you config in json file and add or override some parts from command line arguments.
Like so

`python some.py --conf.some_setting some_value --conf.other_setting "$(<conf.json)"`
