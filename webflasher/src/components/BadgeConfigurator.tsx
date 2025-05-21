import { useEffect, useState } from "react";
import { useMicroPython } from "../MicroPythonContext";
import semver from "semver";
import AppManager from "./apps/AppManager";
import { App } from "./apps/AppListItem";

interface ConfigurationAttrs {
    // all of these are synchronized with the device
    userName: string;
    userHandle: string;
    userPronouns: string;
}

export default function BadgeConfigurator() {
    const { isConnected, mp } = useMicroPython();
    const [config, setConfig] = useState<ConfigurationAttrs>({
        userName: "",
        userPronouns: "",
        userHandle: "",
    });
    const [status, setStatus] = useState<string>("");
    const [firmware, setFirmware] = useState<{ files: { path: string, content: Uint8Array }[], folders: string[] } | 'NOTFETCHED' | 'UPTODATE'>('NOTFETCHED');
    const [apps, setApps] = useState<App[]>([]);

    async function scanForApps(files: any[]) {
        if (!mp) return;
        
        const appsFolder = files.find(f => f.path === "/apps" && f.type === "folder");
        if (!appsFolder) return;

        const newApps: App[] = [];
        const appFolders = appsFolder.childNodes

        for (const appFolder of appFolders) {
            const manifestPath = `${appFolder.path}/manifest.json`;
            if (appFolder.childNodes.find((f: any) => f.path === manifestPath)) {
                try {
                    const manifestContent = await mp.downloadFileToString(manifestPath);
                    const manifest = JSON.parse(manifestContent);
                    if (manifest.displayName && manifest.logoPath && typeof manifest.appNumber === 'number') {
                        newApps.push({
                            manifest,
                            path: appFolder.path
                        });
                    }
                } catch (error) {
                    console.error(`Failed to load manifest for ${appFolder.path}:`, error);
                }
            }
        }

        setApps(newApps);
    }

    useEffect(() => {
        (async () => {
            if (isConnected && mp) {
                const files: any[] = await mp.listFiles();
                console.log("Files on device:", files);
                
                // Scan for apps
                await scanForApps(files);

                if (files.find(file => file.path === "/config.json")) {
                    const data = await mp.downloadFileToString("/config.json");
                    console.log("Config data:", data);
                    try {
                        const parsedConfig = JSON.parse(data) as ConfigurationAttrs;
                        setConfig(parsedConfig);
                    } catch (error) {
                        console.error("Failed to parse config.json:", error);
                    }
                } else {
                    console.warn("config.json not found on the device.");
                }
                if (firmware === 'NOTFETCHED') {
                    setStatus("Fetching firmware version...");
                    const versionResponse = await fetch("https://api.github.com/repos/mpkendall/shipwrecked-pcb/contents/Code/VERSION?ref=deploy");
                    const versionData = await versionResponse.json();
                    const latestVersion = atob(versionData.content);
                    console.log("Latest firmware version:", latestVersion);
                    
                    // get the version on the device
                    setStatus("Checking device firmware version...");
                    const deviceVersion = await mp.downloadFileToString("/VERSION");
                    console.log("Device firmware version:", deviceVersion);
                    if (semver.valid(deviceVersion) && !semver.lt(deviceVersion, latestVersion)) {
                        setStatus("Device firmware is up to date.");
                        setFirmware('UPTODATE'); // no firmware update needed
                    } else {
                        setStatus("Fetching firmware update...");
                        // Fetch the latest release
                        const releasesResponse = await fetch("https://api.github.com/repos/mpkendall/shipwrecked-pcb/releases/latest");
                        const releaseData = await releasesResponse.json();
                        const firmwareAsset = releaseData.assets.find((asset: any) => asset.name === "firmware.zip");
                        
                        if (!firmwareAsset) {
                            throw new Error("Firmware zip not found in latest release");
                        }

                        // Download the firmware zip
                        const zipResponse = await fetch("https://proxy.corsfix.com/?" + firmwareAsset.browser_download_url);
                        const zipBlob = await zipResponse.blob();
                        await handleFirmwareZipBlob(zipBlob);
                    }
                }
            }
            else if (!isConnected) {
                setStatus("Not connected to the device.");
            }
        })();
    }, [isConnected, mp, firmware]);

    function handleSave(): void {
        if (isConnected && mp) {
            const configData = JSON.stringify(config, null, 2);
            console.log("Saving configuration:", configData);
            setStatus("Saving configuration...");
            mp.uploadFileFromString("/config.json", configData)
                .then(() => {
                    console.log("Configuration saved successfully.");
                    setStatus("Configuration saved successfully.");
                })
                .catch((error) => {
                    console.error("Failed to save configuration:", error);
                    setStatus("Failed to save configuration.");
                });
        } else {
            console.warn("Not connected to the device.");
        }
    }

    function handleWipeBadge(): void {
        if (isConnected && mp) {
            const confResponse = window.confirm("Are you sure you want to wipe the badge? This will remove all files, apps and settings.");
            if (!confResponse) {
                setStatus("Wipe cancelled.");
                return;
            }
            setStatus("Wiping badge...");
            mp.removeFolder("/")
                .then(() => {
                    console.log("Badge wiped successfully.");
                    setStatus("Badge wiped successfully.");
                    setFirmware('NOTFETCHED');
                })
                .catch((error) => {
                    console.error("Failed to wipe badge:", error);
                    setStatus("Failed to wipe badge.");
                });
        }
    }

    async function handleFirmwareZipBlob(zipBlob: Blob): Promise<void> {
        // Load and parse the zip file
        const JSZip = (await import('jszip')).default;
        const zip = new JSZip();
        const zipContent = await zip.loadAsync(zipBlob);
        
        // Extract files and folders
        const firmwareFolders: string[] = [];
        const firmwareFilesData: { path: string, content: Uint8Array }[] = [];
        
        for (const [path, file] of Object.entries(zipContent.files)) {
            if (file.dir) {
                firmwareFolders.push("/" + path.slice(0, -1)); // remove trailing slash
            } else {
                const content = await file.async('uint8array');
                firmwareFilesData.push({
                    path: '/' + path,
                    content
                });
            }
        }
        // Move the VERSION file to the end of the files array
        const versionFileIndex = firmwareFilesData.findIndex(f => f.path == '/VERSION');
        if (versionFileIndex !== -1) {
            const [versionFile] = firmwareFilesData.splice(versionFileIndex, 1);
            firmwareFilesData.push(versionFile);
        }

        console.log("Folders:", firmwareFolders);
        console.log("Firmware files:", firmwareFilesData.map(f => f.path));
        setFirmware({ files: firmwareFilesData, folders: firmwareFolders });
        setStatus("Firmware update available.");
    }

    async function uploadFirmware() {
        if (isConnected && mp && firmware !== 'UPTODATE' && firmware !== 'NOTFETCHED') {
            setStatus("Uploading firmware...");
            // first, create the folders
            // we can't do this in parallel unfortunately
            for (const folder of firmware.folders) {
                console.log("Creating folder:", folder);
                setStatus(`Creating folder: ${folder}`);
                await mp.createFolder(folder);
            }
            // then upload the files
            for (const file of firmware.files) {
                console.log("Uploading file:", file.path);
                setStatus(`Uploading file: ${file.path}`);
                await mp.uploadFile(file.path, file.content);
            }
            setStatus("Firmware uploaded successfully.");
            setFirmware('UPTODATE');
        }
    }

    async function handleCustomFirmware(event: React.ChangeEvent<HTMLInputElement>): Promise<void> {
        if (!event.target.files || !event.target.files[0]) {
            return;
        }
        const file = event.target.files[0];
        if (!file.name.endsWith('.zip')) {
            setStatus("Error: Please select a .zip file");
            return;
        }
        setStatus("Processing custom firmware...");
        try {
            await handleFirmwareZipBlob(file);
        } catch (error) {
            console.error("Failed to process custom firmware:", error);
            setStatus("Failed to process custom firmware.");
        }
        setStatus("Custom firmware ready to upload.");
    }

    function handleUploadFirmwareButton(): void {
        (async () => {
        await uploadFirmware();
    })();
    }

    const fields = (
        <div>
        <div>
                <label>
                    Your Name:
                    <input
                        type="text"
                        value={config.userName}
                        disabled={!isConnected}
                        onChange={(e) => setConfig({ ...config, userName: e.target.value })}
                    />
                </label>
            </div>
            <div>
                <label>
                    Pronouns:
                    <input
                        type="text"
                        value={config.userPronouns}
                        disabled={!isConnected}
                        onChange={(e) => setConfig({ ...config, userPronouns: e.target.value })}
                    />
                </label>
            </div>
            <div>
                <label>
                    Slack Handle: @
                    <input
                        type="text"
                        value={config.userHandle}
                        disabled={!isConnected}
                        onChange={(e) => setConfig({ ...config, userHandle: e.target.value })}
                    />
                </label>
            </div>

            <div>
                <button onClick={handleSave}>Save To Badge</button>
            </div>
            </div>
    )

    const firmwareUpdate = (
        <div>
            <h3>Firmware Update</h3>
            <button onClick={handleUploadFirmwareButton}>Upload Firmware</button>
        </div>
    );

    const customOperations = (
        <div>
                <button onClick={handleWipeBadge}>Wipe Badge</button>
                <input 
                    type="file" 
                    accept=".zip"
                    onChange={handleCustomFirmware}
                    style={{ display: 'none' }}
                    id="custom-firmware-input"
                />
                <button onClick={() => document.getElementById('custom-firmware-input')?.click()}>
                    Load Custom Firmware
                </button>
            </div>
    )

    return (
        <div>
            <h2>Badge Configurator</h2>
            <p>Status: {status}</p>
            {isConnected && firmware === 'UPTODATE' ? fields : null}
            {isConnected && firmware !== 'UPTODATE' ? firmwareUpdate : null}
            {isConnected && firmware === 'UPTODATE' ? (
                <AppManager 
                    apps={apps}
                    onAppListChange={() => {
                        if (mp) {
                            mp.listFiles().then(files => scanForApps(files));
                        }
                    }}
                />
            ) : null}
            {isConnected ? customOperations : null}
        </div>
    );
}