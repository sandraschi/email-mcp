# Per-repo fleet start config for email-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'email-mcp'
    BackendPort  = 10813
    FrontendPort = 10812
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\email-mcp\webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'email_mcp.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10813' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
