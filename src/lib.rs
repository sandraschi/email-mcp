use zed_extension_api as zed;

struct EmailManagementExtension;

impl zed::Extension for EmailManagementExtension {
    fn new() -> Self {
        Self
    }

    fn context_server_command(
        &mut self,
        id: &zed::ContextServerId,
        _project: &zed::Project,
    ) -> zed::Result<zed::Command> {
        match id.as_ref() {
            "minimail-mcp" => Ok(zed::Command {
                command: "uv".to_string(),
                args: vec!["run".to_string(), "minimail-mcp.main:main".to_string()],
                env: Default::default(),
            }),
            _ => Err(format!("Unknown server: {}", id.as_ref())),
        }
    }
}

zed::register_extension!(EmailManagementExtension);
