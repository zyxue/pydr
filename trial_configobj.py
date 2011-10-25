from configobj import ConfigObj
import validate

config = ConfigObj('pydr_dc/config.ini.example')

print config['job']
