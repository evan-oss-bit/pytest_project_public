from flasgger import Swagger

swag_desc = """
<div>
<div><p>PYTestTools相关接口</p></div>
<div>
<br>
</div></div>
"""
swagger_config = Swagger.DEFAULT_CONFIG
swagger_config['specs_route'] = '/'
swagger_config['title'] = "PYTestTools相关接口"  # 配置大标题
# swagger_config['description'] = """<a target="_blank" href="/token/" rel="noopener noreferrer" class="link"><font size="6" color="green">跳转Token获取/上传素材/远程执行命令接口工具</font></a>"""
swagger_config['description'] = swag_desc
swagger_config['termsOfService'] = ""
# swagger_config['title'] = config.SWAGGER_TITLE  # 配置大标题
# swagger_config['description'] = config.SWAGGER_DESC  # 配置公共描述内容
# swagger_config['host'] = config.SWAGGER_HOST  # 请求域名

# swagger_config['swagger_ui_bundle_js'] = '//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js'
# swagger_config['swagger_ui_standalone_preset_js'] = '//unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js'
# swagger_config['jquery_js'] = '//unpkg.com/jquery@2.2.4/dist/jquery.min.js'
# swagger_config['swagger_ui_css'] = '//unpkg.com/swagger-ui-dist@3/swagger-ui.css'
