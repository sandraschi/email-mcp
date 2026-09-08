# Per-repo fleet start config for email-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'email-mcp'
    BackendPort  = 10813
    FrontendPort = 10812
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\email-mcp\webapp'
    Backend = @{
        # 'nssm', not 'uvicorn' -- this backend runs as a persistent NSSM
        # Windows service (service name 'email-mcp', matches Name above).
        # With Kind='uvicorn' the generic port-conflict path only health-
        # checks an already-running backend when -ReuseIfRunning is passed;
        # without it, a healthy NSSM-held port gets reported as blocked and
        # the launcher exits 1 -- an instacrash on plain double-click even
        # though the service is fine. Same bug found and fixed in
        # discord-mcp's fleet-start.config.ps1, 2026-09-08.
        Kind          = 'nssm'
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
