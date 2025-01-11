Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create the main form
$form = New-Object System.Windows.Forms.Form
$form.Text = 'QuizMasterPro Process Manager'
$form.Size = New-Object System.Drawing.Size(600,400)
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
$backendGroup.Size = New-Object System.Drawing.Size(565,120)
$backendGroup.Text = "Backend Process"

$backendStatus = New-Object System.Windows.Forms.Label
$backendStatus.Location = New-Object System.Drawing.Point(20,30)
$backendStatus.Size = New-Object System.Drawing.Size(400,20)
$backendStatus.Text = "Status: Not Running"

$startBackend = New-Object System.Windows.Forms.Button
$startBackend.Location = New-Object System.Drawing.Point(20,60)
$startBackend.Size = New-Object System.Drawing.Size(150,40)
$startBackend.Text = "Start Backend"
$startBackend.BackColor = [System.Drawing.Color]::LightGreen

$stopBackend = New-Object System.Windows.Forms.Button
$stopBackend.Location = New-Object System.Drawing.Point(200,60)
$stopBackend.Size = New-Object System.Drawing.Size(150,40)
$stopBackend.Text = "Stop Backend"
$stopBackend.BackColor = [System.Drawing.Color]::LightCoral
$stopBackend.Enabled = $false

$focusBackend = New-Object System.Windows.Forms.Button
$focusBackend.Location = New-Object System.Drawing.Point(380,60)
$focusBackend.Size = New-Object System.Drawing.Size(150,40)
$focusBackend.Text = "Bring to Front"
$focusBackend.BackColor = [System.Drawing.Color]::LightBlue
$focusBackend.Enabled = $false

$backendGroup.Controls.AddRange(@($backendStatus, $startBackend, $stopBackend, $focusBackend))

# Frontend Group
$frontendGroup = New-Object System.Windows.Forms.GroupBox
$frontendGroup.Location = New-Object System.Drawing.Point(10,230)
$frontendGroup.Size = New-Object System.Drawing.Size(565,120)
$frontendGroup.Text = "Frontend Process"

$frontendStatus = New-Object System.Windows.Forms.Label
$frontendStatus.Location = New-Object System.Drawing.Point(20,30)
$frontendStatus.Size = New-Object System.Drawing.Size(400,20)
$frontendStatus.Text = "Status: Not Running"

$startFrontend = New-Object System.Windows.Forms.Button
$startFrontend.Location = New-Object System.Drawing.Point(20,60)
$startFrontend.Size = New-Object System.Drawing.Size(150,40)
$startFrontend.Text = "Start Frontend"
$startFrontend.BackColor = [System.Drawing.Color]::LightGreen

$stopFrontend = New-Object System.Windows.Forms.Button
$stopFrontend.Location = New-Object System.Drawing.Point(200,60)
$stopFrontend.Size = New-Object System.Drawing.Size(150,40)
$stopFrontend.Text = "Stop Frontend"
$stopFrontend.BackColor = [System.Drawing.Color]::LightCoral
$stopFrontend.Enabled = $false

$focusFrontend = New-Object System.Windows.Forms.Button
$focusFrontend.Location = New-Object System.Drawing.Point(380,60)
$focusFrontend.Size = New-Object System.Drawing.Size(150,40)
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

# Backend Button Click Events
$startBackend.Add_Click({
    $env = Get-SelectedEnvironment
    $backendStatus.Text = "Status: Starting..."
    $startBackend.Enabled = $false
    
    # Start the backend process
    $script:backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c _start_backend.bat $env" -PassThru -WindowStyle Normal
    
    $backendStatus.Text = "Status: Running (PID: $($script:backendProcess.Id))"
    $stopBackend.Enabled = $true
    $focusBackend.Enabled = $true
})

$stopBackend.Add_Click({
    if ($script:backendProcess -ne $null) {
        # Kill the process tree
        $children = Get-CimInstance -Class Win32_Process -Filter "ParentProcessId=$($script:backendProcess.Id)"
        foreach ($child in $children) {
            Stop-Process -Id $child.ProcessId -Force
        }
        Stop-Process -Id $script:backendProcess.Id -Force
        
        $script:backendProcess = $null
        $backendStatus.Text = "Status: Not Running"
        $stopBackend.Enabled = $false
        $focusBackend.Enabled = $false
        $startBackend.Enabled = $true
    }
})

$focusBackend.Add_Click({
    if ($script:backendProcess -ne $null) {
        try {
            # Get the main window handle
            $proc = Get-Process -Id $script:backendProcess.Id -ErrorAction SilentlyContinue
            if ($proc -and $proc.MainWindowHandle) {
                [Win32]::ShowWindow($proc.MainWindowHandle, [Win32]::SW_RESTORE)
                [Win32]::SetForegroundWindow($proc.MainWindowHandle)
            }
        } catch {
            Write-Host "Could not bring window to front: $_"
        }
    }
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
        # Kill the process tree
        $children = Get-CimInstance -Class Win32_Process -Filter "ParentProcessId=$($script:frontendProcess.Id)"
        foreach ($child in $children) {
            Stop-Process -Id $child.ProcessId -Force
        }
        Stop-Process -Id $script:frontendProcess.Id -Force
        
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

# Show the form
$form.ShowDialog()
