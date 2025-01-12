Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create the main form
$form = New-Object System.Windows.Forms.Form
$form.Text = 'QuizMasterPro Process Manager'
$form.Size = New-Object System.Drawing.Size(600,450)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false

# Environment Selection Group
$envGroup = New-Object System.Windows.Forms.GroupBox
$envGroup.Location = New-Object System.Drawing.Point(10,10)
$envGroup.Size = New-Object System.Drawing.Size(565,80)
$envGroup.Text = "Environment Selection"

# Environment Radio Buttons
$envDev = New-Object System.Windows.Forms.RadioButton
$envDev.Location = New-Object System.Drawing.Point(20,30)
$envDev.Size = New-Object System.Drawing.Size(150,20)
$envDev.Text = "Development"
$envDev.Checked = $true

$envTest = New-Object System.Windows.Forms.RadioButton
$envTest.Location = New-Object System.Drawing.Point(200,30)
$envTest.Size = New-Object System.Drawing.Size(150,20)
$envTest.Text = "Test"

$envProd = New-Object System.Windows.Forms.RadioButton
$envProd.Location = New-Object System.Drawing.Point(380,30)
$envProd.Size = New-Object System.Drawing.Size(150,20)
$envProd.Text = "Production"

$envGroup.Controls.AddRange(@($envDev, $envTest, $envProd))

# Backend Group
$backendGroup = New-Object System.Windows.Forms.GroupBox
$backendGroup.Location = New-Object System.Drawing.Point(10,100)
$backendGroup.Size = New-Object System.Drawing.Size(565,140)
$backendGroup.Text = "Backend Process"

$backendStatus = New-Object System.Windows.Forms.Label
$backendStatus.Location = New-Object System.Drawing.Point(10,20)
$backendStatus.Size = New-Object System.Drawing.Size(535,20)
$backendStatus.Text = "Status: Not Running"

$startBackend = New-Object System.Windows.Forms.Button
$startBackend.Location = New-Object System.Drawing.Point(10,50)
$startBackend.Size = New-Object System.Drawing.Size(100,30)
$startBackend.Text = "Start Backend"
$startBackend.BackColor = [System.Drawing.Color]::LightGreen

$stopBackend = New-Object System.Windows.Forms.Button
$stopBackend.Location = New-Object System.Drawing.Point(120,50)
$stopBackend.Size = New-Object System.Drawing.Size(100,30)
$stopBackend.Text = "Stop Backend"
$stopBackend.BackColor = [System.Drawing.Color]::LightPink
$stopBackend.Enabled = $false

$focusBackend = New-Object System.Windows.Forms.Button
$focusBackend.Location = New-Object System.Drawing.Point(230,50)
$focusBackend.Size = New-Object System.Drawing.Size(100,30)
$focusBackend.Text = "View Logs"
$focusBackend.BackColor = [System.Drawing.Color]::LightBlue
$focusBackend.Enabled = $false

$rebuildBackend = New-Object System.Windows.Forms.Button
$rebuildBackend.Location = New-Object System.Drawing.Point(340,50)
$rebuildBackend.Size = New-Object System.Drawing.Size(100,30)
$rebuildBackend.Text = "Rebuild Image"
$rebuildBackend.BackColor = [System.Drawing.Color]::LightYellow

$cleanRebuildBackend = New-Object System.Windows.Forms.Button
$cleanRebuildBackend.Location = New-Object System.Drawing.Point(450,50)
$cleanRebuildBackend.Size = New-Object System.Drawing.Size(100,30)
$cleanRebuildBackend.Text = "Clean Rebuild"
$cleanRebuildBackend.BackColor = [System.Drawing.Color]::LightYellow

$backendGroup.Controls.AddRange(@($backendStatus, $startBackend, $stopBackend, $focusBackend, $rebuildBackend, $cleanRebuildBackend))

# Frontend Group
$frontendGroup = New-Object System.Windows.Forms.GroupBox
$frontendGroup.Location = New-Object System.Drawing.Point(10,250)
$frontendGroup.Size = New-Object System.Drawing.Size(565,140)
$frontendGroup.Text = "Frontend Process"

$frontendStatus = New-Object System.Windows.Forms.Label
$frontendStatus.Location = New-Object System.Drawing.Point(10,20)
$frontendStatus.Size = New-Object System.Drawing.Size(535,20)
$frontendStatus.Text = "Status: Not Running"

$startFrontend = New-Object System.Windows.Forms.Button
$startFrontend.Location = New-Object System.Drawing.Point(10,50)
$startFrontend.Size = New-Object System.Drawing.Size(120,30)
$startFrontend.Text = "Start Frontend"
$startFrontend.BackColor = [System.Drawing.Color]::LightGreen

$stopFrontend = New-Object System.Windows.Forms.Button
$stopFrontend.Location = New-Object System.Drawing.Point(140,50)
$stopFrontend.Size = New-Object System.Drawing.Size(120,30)
$stopFrontend.Text = "Stop Frontend"
$stopFrontend.BackColor = [System.Drawing.Color]::LightPink
$stopFrontend.Enabled = $false

$focusFrontend = New-Object System.Windows.Forms.Button
$focusFrontend.Location = New-Object System.Drawing.Point(270,50)
$focusFrontend.Size = New-Object System.Drawing.Size(120,30)
$focusFrontend.Text = "Bring to Front"
$focusFrontend.BackColor = [System.Drawing.Color]::LightBlue
$focusFrontend.Enabled = $false

$frontendGroup.Controls.AddRange(@($frontendStatus, $startFrontend, $stopFrontend, $focusFrontend))

# Add all groups to the form
$form.Controls.AddRange(@($envGroup, $backendGroup, $frontendGroup))

# Backend Process Variable
$script:backendProcess = $null
$script:frontendProcess = $null

# Get selected environment
function Get-SelectedEnvironment {
    if ($envDev.Checked) { return "development" }
    if ($envTest.Checked) { return "test" }
    if ($envProd.Checked) { return "production" }
}

# Function to load environment variables from .env file
function Load-EnvFile {
    param (
        [string]$Environment
    )
    
    $envFile = Join-Path $PSScriptRoot "..\backend\.env.$Environment"
    $envVars = @{}
    
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Remove quotes if present
                $value = $value -replace '^[''"]|[''"]$'
                $envVars[$key] = $value
            }
        }
    } else {
        Write-Host "Warning: No .env.$Environment file found at $envFile"
        # Set default values
        $envVars = @{
            "QUIZMASTER_POSTGRES_USER" = "test_user"
            "QUIZMASTER_POSTGRES_PASSWORD" = "test_password"
            "QUIZMASTER_POSTGRES_PORT" = "5432"
            "QUIZMASTER_POSTGRES_HOST" = "host.docker.internal"
            "QUIZMASTER_DEBUG" = "true"
            "QUIZMASTER_LOG_LEVEL" = "DEBUG"
        }
    }
    
    return $envVars
}

# Function to build Docker environment arguments
function Get-DockerEnvArgs {
    param (
        [string]$Environment,
        [hashtable]$EnvVars
    )
    
    $args = @()
    # Always set the environment
    $args += "-e", "QUIZMASTER_ENVIRONMENT=$Environment"
    
    # Add all environment variables
    foreach ($key in $EnvVars.Keys) {
        $value = $EnvVars[$key]
        $args += "-e", "${key}=${value}"
    }
    
    return $args
}

# Function to check if Docker image exists
function Test-DockerImage {
    param (
        [string]$ImageName
    )
    $image = docker images -q $ImageName 2>&1
    return $image -ne $null -and $image -ne ""
}

# Function to format timespan
function Format-TimeSpan {
    param (
        [TimeSpan]$TimeSpan
    )
    
    if ($TimeSpan.TotalHours -ge 1) {
        return "{0:h'h 'm'm 's's'}" -f $TimeSpan
    } elseif ($TimeSpan.TotalMinutes -ge 1) {
        return "{0:m'm 's's'}" -f $TimeSpan
    } else {
        return "{0:s\.f's'}" -f $TimeSpan
    }
}

# Function to update status with elapsed time
function Update-StatusWithTime {
    param (
        [DateTime]$StartTime,
        [string]$Status
    )
    
    $elapsed = (Get-Date) - $StartTime
    $elapsedStr = Format-TimeSpan -TimeSpan $elapsed
    $backendStatus.Text = "$Status (Elapsed: $elapsedStr)"
}

# Timer for rebuild status
$script:rebuildTimer = $null

function Start-RebuildTimer {
    param (
        [DateTime]$StartTime,
        [string]$Status
    )
    
    $script:rebuildTimer = New-Object System.Windows.Forms.Timer
    $script:rebuildTimer.Interval = 100  # Update every 100ms
    $script:rebuildTimer.Add_Tick({
        Update-StatusWithTime -StartTime $StartTime -Status $Status
    })
    $script:rebuildTimer.Start()
}

function Stop-RebuildTimer {
    if ($script:rebuildTimer) {
        $script:rebuildTimer.Stop()
        $script:rebuildTimer.Dispose()
        $script:rebuildTimer = $null
    }
}

# Function to manage Docker container
function Manage-DockerContainer {
    param (
        [string]$Action,
        [string]$Environment
    )
    
    $containerName = "quizmaster-backend"
    $imageName = "quizmaster-backend:latest"
    $backendPath = Join-Path $PSScriptRoot "..\backend"
    
    switch ($Action) {
        "start" {
            Write-Host "Starting Docker container for $Environment environment..."
            
            # Check for requirements.txt
            $requirementsPath = Join-Path $backendPath "requirements.txt"
            if (-not (Test-Path $requirementsPath)) {
                Write-Host "Error: requirements.txt not found at $requirementsPath"
                return $null
            }
            
            # Stop and remove existing container if it exists
            Write-Host "Cleaning up any existing containers..."
            docker stop $containerName 2>&1 | Out-Null
            docker rm $containerName 2>&1 | Out-Null
            
            # Only build if image doesn't exist
            if (-not (Test-DockerImage $imageName)) {
                Write-Host "Docker image not found. Building new image..."
                Write-Host "Using backend path: $backendPath"
                Set-Location $backendPath
                $buildOutput = docker build -t $imageName . 2>&1
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "Failed to build Docker image:"
                    Write-Host $buildOutput
                    return $null
                }
            } else {
                Write-Host "Using existing Docker image..."
            }
            
            # Load environment variables
            $envVars = Load-EnvFile -Environment $Environment
            $envArgs = Get-DockerEnvArgs -Environment $Environment -EnvVars $envVars
            
            # Start the container with the correct environment
            Write-Host "Starting Docker container..."
            
            # Build the docker run command
            $dockerArgs = @(
                "run", "-d",
                "--name", $containerName,
                "-p", "8000:8000"
            )
            $dockerArgs += $envArgs
            
            # Mount the code directory
            $dockerArgs += @("-v", "${backendPath}:/app")
            
            # Mount the environment file
            $envFile = Join-Path $backendPath ".env.$Environment"
            if (Test-Path $envFile) {
                Write-Host "Mounting .env.$Environment file..."
                $dockerArgs += @("-v", "${envFile}:/app/.env.$Environment")
            } else {
                Write-Host "Warning: No .env.$Environment file found at $envFile"
            }
            
            $dockerArgs += @($imageName)
            
            Write-Host "Running Docker with args: $($dockerArgs -join ' ')"
            $runOutput = docker $dockerArgs 2>&1
                
            if ($LASTEXITCODE -eq 0) {
                $containerId = $runOutput
                
                # Wait for container to be running
                $maxAttempts = 10
                $attempt = 1
                $containerRunning = $false
                
                while ($attempt -le $maxAttempts) {
                    Write-Host "Checking container status (attempt $attempt of $maxAttempts)..."
                    $status = docker inspect -f '{{.State.Status}}' $containerName 2>&1
                    if ($LASTEXITCODE -eq 0 -and $status -eq "running") {
                        $containerRunning = $true
                        break
                    }
                    Start-Sleep -Seconds 1
                    $attempt++
                }
                
                if ($containerRunning) {
                    Write-Host "Container started successfully with ID: $containerId"
                    # Show initial logs to help diagnose any startup issues
                    Write-Host "Initial container logs:"
                    docker logs $containerName
                    return $containerId
                } else {
                    Write-Host "Container failed to start properly. Logs:"
                    docker logs $containerName
                    Write-Host "Container status:"
                    docker inspect $containerName
                    docker stop $containerName 2>&1 | Out-Null
                    docker rm $containerName 2>&1 | Out-Null
                    return $null
                }
            } else {
                Write-Host "Failed to start container:"
                Write-Host $runOutput
                return $null
            }
        }
        "rebuild" {
            $startTime = Get-Date
            Write-Host "Rebuilding Docker image..."
            
            # Stop and remove existing container if it exists
            Write-Host "Stopping any running containers..."
            docker stop $containerName 2>&1 | Out-Null
            docker rm $containerName 2>&1 | Out-Null
            
            Set-Location $backendPath
            Write-Host "Building new image (with caching)..."
            $buildOutput = docker build -t $imageName . 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Failed to rebuild Docker image:"
                Write-Host $buildOutput
                return @{
                    Success = $false
                    Duration = (Get-Date) - $startTime
                }
            }
            Write-Host "Successfully rebuilt Docker image"
            return @{
                Success = $true
                Duration = (Get-Date) - $startTime
            }
        }
        "rebuild-clean" {
            Write-Host "Rebuilding Docker image from scratch..."
            
            # Stop and remove existing container if it exists
            Write-Host "Stopping any running containers..."
            docker stop $containerName 2>&1 | Out-Null
            docker rm $containerName 2>&1 | Out-Null
            
            # Remove existing image
            Write-Host "Removing existing image..."
            docker rmi $imageName 2>&1 | Out-Null
            
            Set-Location $backendPath
            Write-Host "Building new image (no cache)..."
            $buildOutput = docker build -t $imageName . --no-cache 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Failed to rebuild Docker image:"
                Write-Host $buildOutput
                return $false
            }
            Write-Host "Successfully rebuilt Docker image"
            return $true
        }
        "stop" {
            Write-Host "Stopping Docker container..."
            $stopOutput = docker stop $containerName 2>&1
            Write-Host $stopOutput
            $rmOutput = docker rm $containerName 2>&1
            Write-Host $rmOutput
        }
        "logs" {
            # Check if container exists and is running
            $status = docker inspect -f '{{.State.Status}}' $containerName 2>&1
            if ($LASTEXITCODE -eq 0 -and $status -eq "running") {
                docker logs -f $containerName
            } else {
                Write-Host "Container is not running. Current status: $status"
                Write-Host "Recent logs:"
                docker logs $containerName 2>&1
                return $false
            }
        }
        "status" {
            $status = docker inspect -f '{{.State.Status}}' $containerName 2>&1
            if ($LASTEXITCODE -eq 0) {
                return $status
            }
            return "not_found"
        }
    }
}

# Backend Button Click Events
$startBackend.Add_Click({
    $env = Get-SelectedEnvironment
    $backendStatus.Text = "Status: Starting Docker container..."
    $startBackend.Enabled = $false
    $stopBackend.Enabled = $false
    $focusBackend.Enabled = $false
    
    # Start Docker container
    $containerId = Manage-DockerContainer -Action "start" -Environment $env
    
    if ($containerId) {
        $script:backendProcess = $containerId
        $shortId = $containerId.Substring(0, [Math]::Min(12, $containerId.Length))
        $backendStatus.Text = "Status: Running in Docker (Container: $shortId)"
        $stopBackend.Enabled = $true
        $focusBackend.Enabled = $true
    } else {
        $backendStatus.Text = "Status: Failed to start Docker container"
        $startBackend.Enabled = $true
    }
})

# Stop Backend Button Click Event
$stopBackend.Add_Click({
    if ($script:backendProcess) {
        $backendStatus.Text = "Status: Stopping..."
        Manage-DockerContainer -Action "stop"
        $script:backendProcess = $null
        $backendStatus.Text = "Status: Stopped"
        $startBackend.Enabled = $true
        $stopBackend.Enabled = $false
        $focusBackend.Enabled = $false
    }
})

# Focus Backend Button Click Event
$focusBackend.Add_Click({
    if ($script:backendProcess) {
        $status = Manage-DockerContainer -Action "status"
        if ($status -eq "running") {
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker logs -f quizmaster-backend"
        } else {
            [System.Windows.Forms.MessageBox]::Show(
                "Container is not running. Current status: $status",
                "Container Status",
                [System.Windows.Forms.MessageBoxButtons]::OK,
                [System.Windows.Forms.MessageBoxIcon]::Warning
            )
        }
    }
})

# Rebuild Backend Button Click Event
$rebuildBackend.Add_Click({
    $rebuildBackend.Enabled = $false
    $startBackend.Enabled = $false
    $stopBackend.Enabled = $false
    $focusBackend.Enabled = $false
    
    $startTime = Get-Date
    $backendStatus.Text = "Status: Starting rebuild..."
    Start-RebuildTimer -StartTime $startTime -Status "Status: Rebuilding Docker image"
    
    $result = Manage-DockerContainer -Action "rebuild"
    Stop-RebuildTimer
    
    if ($result.Success) {
        $duration = Format-TimeSpan -TimeSpan $result.Duration
        $backendStatus.Text = "Status: Rebuild successful ($duration). Ready to start."
        $startBackend.Enabled = $true
    } else {
        $duration = Format-TimeSpan -TimeSpan $result.Duration
        $backendStatus.Text = "Status: Rebuild failed ($duration)"
        $startBackend.Enabled = $true
    }
    $rebuildBackend.Enabled = $true
})

# Clean Rebuild Backend Button Click Event
$cleanRebuildBackend.Add_Click({
    $cleanRebuildBackend.Enabled = $false
    $rebuildBackend.Enabled = $false
    $startBackend.Enabled = $false
    $stopBackend.Enabled = $false
    $focusBackend.Enabled = $false
    $backendStatus.Text = "Status: Rebuilding Docker image from scratch..."
    
    if (Manage-DockerContainer -Action "rebuild-clean") {
        $backendStatus.Text = "Status: Clean rebuild successful. Ready to start."
        $startBackend.Enabled = $true
    } else {
        $backendStatus.Text = "Status: Clean rebuild failed"
        $startBackend.Enabled = $true
    }
    $cleanRebuildBackend.Enabled = $true
    $rebuildBackend.Enabled = $true
})

# Frontend Button Click Events
$startFrontend.Add_Click({
    $env = Get-SelectedEnvironment
    $frontendStatus.Text = "Status: Starting..."
    $startFrontend.Enabled = $false
    
    # Start the frontend process
    $script:frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c _start_frontend.bat $env" -PassThru -WindowStyle Normal
    
    $frontendStatus.Text = "Status: Running (PID: $($script:frontendProcess.Id))"
    $stopFrontend.Enabled = $true
    $focusFrontend.Enabled = $true
})

$stopFrontend.Add_Click({
    if ($script:frontendProcess -ne $null) {
        $frontendStatus.Text = "Status: Stopping..."
        
        # Kill the process tree
        $processesToKill = Get-CimInstance -Class Win32_Process | Where-Object { $_.ParentProcessId -eq $script:frontendProcess.Id -or $_.ProcessId -eq $script:frontendProcess.Id }
        foreach ($process in $processesToKill) {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        }
        
        # Wait for processes to fully terminate
        Start-Sleep -Seconds 2
        
        # Check if any Node.js processes are still running on port 3000
        $runningOnPort = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
        if ($runningOnPort) {
            $processId = $runningOnPort.OwningProcess
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process -and $process.Name -eq "node") {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
        
        $script:frontendProcess = $null
        $frontendStatus.Text = "Status: Not Running"
        $stopFrontend.Enabled = $false
        $focusFrontend.Enabled = $false
        $startFrontend.Enabled = $true
    }
})

$focusFrontend.Add_Click({
    if ($script:frontendProcess -ne $null) {
        try {
            # Get the main window handle
            $proc = Get-Process -Id $script:frontendProcess.Id -ErrorAction SilentlyContinue
            if ($proc -and $proc.MainWindowHandle) {
                [Win32]::ShowWindow($proc.MainWindowHandle, [Win32]::SW_RESTORE)
                [Win32]::SetForegroundWindow($proc.MainWindowHandle)
            }
        } catch {
            Write-Host "Could not bring window to front: $_"
        }
    }
})

# Form Closing Event
$form.Add_FormClosing({
    param($sender, $e)
    
    # Clean up any running processes
    if ($script:backendProcess -ne $null) {
        $stopBackend.PerformClick()
    }
    if ($script:frontendProcess -ne $null) {
        $stopFrontend.PerformClick()
    }
})

# Add Win32 API functions for window management
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    public class Win32 {
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
        
        [DllImport("user32.dll")]
        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        
        public const int SW_RESTORE = 9;
    }
"@

# Add tooltips
$rebuildTooltip = New-Object System.Windows.Forms.ToolTip
$rebuildTooltip.SetToolTip($rebuildBackend, "Rebuild Docker image (only needed when requirements.txt or Dockerfile changes)")

$cleanRebuildTooltip = New-Object System.Windows.Forms.ToolTip
$cleanRebuildTooltip.SetToolTip($cleanRebuildBackend, "Clean Rebuild (No Cache)")

# Show the form
$form.ShowDialog()
