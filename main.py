from regbot import AutoReg

# b = BoilerKey('boilerkey_config.json', 'boilerkey_counter.json')
# print(b.generate_password())


auto_reg = AutoReg('config.toml', None)

# print(auto_reg.fetch_class_info(13241))
auto_reg.start()