import React, { useState, useEffect } from 'react';
import { useMicroPython } from '../../MicroPythonContext';
import { useDeviceState } from '../../DeviceStateContext';
import AppListItem, { App } from './AppListItem';
import './AppManager.css';

interface AppManagerProps {
    apps: App[];
    onAppListChange: (apps: App[]) => void;
}

export default function AppManager({ apps, onAppListChange }: AppManagerProps) {
    const { mp, isConnected } = useMicroPython();
    const [status, setStatus] = useState<string>("");

    const { needsRefresh, setIsScanning, isScanning, firmwareStatus } = useDeviceState();

    useEffect(() => {
        if (isConnected && mp && !isScanning) {
            scanForApps();
        } else if (!isConnected) {
            onAppListChange([]);
        }
    }, [isConnected, mp, needsRefresh]);

    const scanForApps = async () => {
        if (!mp) return;

        setIsScanning(true);
        try {
            setStatus("Scanning for apps...");
            const files = await mp.listFiles();
            console.log("Files on device:", files);

            const appsFolder = files.find((f: { path: string, type: string }) => f.path === "/apps" && f.type === "folder");
            if (!appsFolder) {
                setStatus("No apps folder found");
                onAppListChange([]);
                return;
            }

            const newApps: App[] = [];
            const appFolders = appsFolder.childNodes;

            for (const appFolder of appFolders) {
                console.log(`Found app folder: ${appFolder.path}`);
                const manifestPath = `${appFolder.path}/manifest.json`;
                if (appFolder.childNodes.find((f: any) => f.path === manifestPath)) {
                    try {
                        const manifestContent = await mp.downloadFileToString(manifestPath);
                        console.log(`Loaded manifest for ${appFolder.path}:`, manifestContent);
                        const manifest = JSON.parse(manifestContent);
                        if (manifest.displayName && typeof manifest.appNumber === 'number') {
                            newApps.push({
                                manifest,
                                path: appFolder.path
                            });
                        } else {
                            console.warn(`Invalid manifest for ${appFolder.path}:`, manifest);
                        }
                    } catch (error) {
                        console.error(`Failed to load manifest for ${appFolder.path}:`, error);
                    }
                }
            }

            onAppListChange(newApps);
            setStatus(newApps.length ? `Found ${newApps.length} apps` : "No apps installed");
            console.log("Found apps:", newApps);
        } catch (error) {
            console.error("Failed to scan for apps:", error);
            setStatus("Failed to scan for apps");
            onAppListChange([]);
        } finally {
            setIsScanning(false);
        }
    };

    const handleAppUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (!event.target.files || !event.target.files[0] || !mp) return;

        const file = event.target.files[0];
        if (!file.name.endsWith('.zip')) {
            setStatus("Error: Please select a .zip file");
            return;
        }

        setIsScanning(true);
        try {
            setStatus("Processing app upload...");
            const JSZip = (await import('jszip')).default;
            const zip = new JSZip();
            const zipContent = await zip.loadAsync(file);
            
            // Verify manifest.json exists in the root
            const manifestFile = zipContent.files['manifest.json'];
            if (!manifestFile) {
                setStatus("Error: Invalid app package (missing manifest.json)");
                return;
            }

            // Parse and validate manifest
            const manifestContent = await manifestFile.async('text');
            const manifest = JSON.parse(manifestContent);
            if (!manifest.displayName || typeof manifest.appNumber !== 'number') {
                setStatus("Error: Invalid manifest.json (missing required fields: displayName or appNumber, and appNumber must be an integer)");
                return;
            }

            // Create app directory
            const appPath = `/apps/${manifest.displayName.replace(/[^a-zA-Z0-9_\-]/g, '_')}`;
            await mp.createFolder(appPath);

            // Upload all files
            for (const [path, file] of Object.entries(zipContent.files)) {
                if (!file.dir) {
                    const content = await file.async('uint8array');
                    await mp.uploadFile(`${appPath}/${path}`, content);
                }
            }

            setStatus("App uploaded successfully");
            const updatedApps = [...apps, {
                path: appPath,
                manifest: manifest,
            }];
            onAppListChange(updatedApps);
        } catch (error) {
            console.error("Failed to upload app:", error);
            setStatus("Failed to upload app");
        }
    };

    const handleAppDelete = async (app: App) => {
        if (!mp) return;

        try {
            setStatus(`Deleting ${app.manifest.displayName}...`);
            await mp.removeFolder(app.path);
            setStatus(`${app.manifest.displayName} deleted successfully`);
            const updatedApps = apps.filter(a => a.path !== app.path);
            onAppListChange(updatedApps);
        } catch (error) {
            console.error("Failed to delete app:", error);
            setStatus(`Failed to delete ${app.manifest.displayName}`);
        }
    };

    const isDeviceBusy = firmwareStatus === 'updating' || isScanning;
    const canUploadApp = isConnected && !isDeviceBusy;

    return (
        <div className="app-manager">
            <h3>App Management</h3>
            {status && <div className={`status-message ${status.includes("Error") ? "error" : ""}`}>{status}</div>}
            
            <div className="app-upload">
                <input
                    type="file"
                    accept=".zip"
                    onChange={handleAppUpload}
                    style={{ display: 'none' }}
                    id="app-upload-input"
                    disabled={!canUploadApp}
                />
                <button 
                    className="button primary"
                    onClick={() => document.getElementById('app-upload-input')?.click()}
                    disabled={!canUploadApp}
                    title={
                        !isConnected ? "Connect to a device first" :
                        isDeviceBusy ? "Please wait for current operation to complete" :
                        "Upload a new app to the badge"
                    }
                >
                    Upload New App
                </button>
            </div>

            <div className="app-list">
                {isScanning ? (
                    <div className="app-status">Scanning for apps...</div>
                ) : apps.length === 0 ? (
                    <div className="app-status">No apps installed</div>
                ) : (
                    apps.map(app => (
                        <AppListItem
                            key={app.path}
                            app={app}
                            onDelete={handleAppDelete}
                            disabled={isDeviceBusy}
                        />
                    ))
                )}
            </div>
        </div>
    );
}
