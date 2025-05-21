import React, { useEffect, useState } from 'react';
import { useMicroPython } from '../MicroPythonContext';
import { useDeviceState } from '../DeviceStateContext';
import semver from 'semver';
import './FirmwarePanel.css';

export default function FirmwarePanel() {
  const { mp, isConnected } = useMicroPython();
  const { setFirmwareStatus, triggerRefresh, firmwareStatus } = useDeviceState();
  const [firmware, setFirmware] = useState<{ files: { path: string, content: Uint8Array }[], folders: string[] } | 'NOTFETCHED' | 'UPTODATE'>('NOTFETCHED');
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    if (isConnected && mp) {
      checkFirmware();
    } else {
      setFirmware('NOTFETCHED');
      setStatus("");
      setFirmwareStatus('idle');
    }
  }, [isConnected, mp]);

  const checkFirmware = async () => {
    if (!mp) return;

    setFirmwareStatus('checking');
    try {
      setStatus("Checking firmware version...");
      const version = await mp.downloadFileToString("/VERSION");
      console.log("Current firmware version:", version);

      setStatus("Fetching latest version...");
      const versionResponse = await fetch("https://api.github.com/repos/mpkendall/shipwrecked-pcb/contents/Code/VERSION?ref=deploy");
      const versionData = await versionResponse.json();
      const latestVersion = atob(versionData.content);
      console.log("Latest firmware version:", latestVersion);

      if (semver.valid(version) && !semver.lt(version, latestVersion)) {
        setStatus("Device firmware is up to date.");
        setFirmware('UPTODATE');
        setFirmwareStatus('idle');
      } else {
        setStatus("Fetching firmware update...");
        // Fetch firmware.zip from the firmware-zips branch using the GitHub API
        const zipResponse = await fetch(
          "https://api.github.com/repos/mpkendall/shipwrecked-pcb/contents/firmware-zips/firmware.zip?ref=firmware-zips"
        );
        const zipData = await zipResponse.json();
        if (!zipData.content) {
          throw new Error("Firmware zip not found in firmware-zips branch");
        }
        // Decode base64 content to binary
        const binaryString = atob(zipData.content);
        const len = binaryString.length;
        const uint8Array = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
          uint8Array[i] = binaryString.charCodeAt(i);
        }
        const zipBlob = new Blob([uint8Array], { type: "application/zip" });
        await handleFirmwareZipBlob(zipBlob);
        setStatus("Firmware update ready to install.");
      }
    } catch (error) {
      console.error("Failed to check firmware:", error);
      setStatus("Failed to check firmware version");
    }
  };

  const handleFirmwareZipBlob = async (zipBlob: Blob) => {
    try {
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
      const versionFileIndex = firmwareFilesData.findIndex(f => f.path === '/VERSION');
      if (versionFileIndex !== -1) {
        const [versionFile] = firmwareFilesData.splice(versionFileIndex, 1);
        firmwareFilesData.push(versionFile);
      }

      console.log("Folders:", firmwareFolders);
      console.log("Firmware files:", firmwareFilesData.map(f => f.path));
      setFirmware({ files: firmwareFilesData, folders: firmwareFolders });
    } catch (error) {
      console.error("Failed to process firmware zip:", error);
      setStatus("Failed to process firmware package");
      throw error;
    }
  };

  const uploadFirmware = async () => {
    if (!mp || firmware === 'UPTODATE' || firmware === 'NOTFETCHED') return;

    // Check if browser is Firefox
    if (navigator.userAgent.toLowerCase().indexOf('firefox') > -1) {
      const proceed = window.confirm('You are using Firefox. Due to native WebSerial support, the firmware update process will be significantly faster in Chrome or other Chromium-based browsers. Do you want to continue anyway?');
      if (!proceed) return;
    }

    setFirmwareStatus('updating');
    try {
      setStatus("Uploading firmware...");
      // Create folders first
      for (const folder of firmware.folders) {
        console.log("Creating folder:", folder);
        setStatus(`Creating folder: ${folder}`);
        await mp.createFolder(folder);
      }

      // Then upload files
      for (const file of firmware.files) {
        console.log("Uploading file:", file.path);
        setStatus(`Uploading file: ${file.path}`);
        await mp.uploadFile(file.path, file.content);
      }

      setStatus("Firmware uploaded successfully.");
      setFirmware('UPTODATE');
      setFirmwareStatus('idle');
      // Trigger refresh for other components
      triggerRefresh();
    } catch (error) {
      console.error("Failed to upload firmware:", error);
      setStatus("Failed to upload firmware");
      setFirmwareStatus('idle');
    }
  };

  const handleCustomFirmware = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || !event.target.files[0]) return;

    const file = event.target.files[0];
    if (!file.name.endsWith('.zip')) {
      setStatus("Error: Please select a .zip file");
      return;
    }

    setFirmwareStatus('updating');
    setStatus("Processing custom firmware...");
    try {
      await handleFirmwareZipBlob(file);
      setStatus("Custom firmware ready to install.");
      setFirmwareStatus('ready');
    } catch (error) {
      console.error("Failed to process custom firmware:", error);
      setStatus("Failed to process custom firmware");
      setFirmwareStatus('idle');
    }
  };

  const handleWipeBadge = async () => {
    if (!mp || !isConnected) return;

    const confirmed = window.confirm(
      "Are you sure you want to wipe the badge? This will remove all files, apps and settings."
    );

    if (!confirmed) {
      setStatus("Wipe cancelled.");
      return;
    }

    try {
      setStatus("Wiping badge...");
      await mp.removeFolder("/");
      setStatus("Badge wiped successfully.");
      setFirmware('NOTFETCHED');
      setFirmwareStatus('idle');
      // Trigger refresh for other components
      triggerRefresh();
    } catch (error) {
      console.error("Failed to wipe badge:", error);
      setStatus("Failed to wipe badge");
      setFirmwareStatus('idle');
    }
  };

  return (
    <div className="firmware-panel">
      <h2>Firmware Update</h2>
      <div className="firmware-status">
        {status && <div className="status-message">{status}</div>}
      </div>
      <div className="firmware-actions">
        <button 
          className="button primary" 
          onClick={checkFirmware}
          disabled={!isConnected}
        >
          Check for Updates
        </button>

        {firmware !== 'NOTFETCHED' && firmware !== 'UPTODATE' && (
          <button 
            className="button primary"
            onClick={uploadFirmware}
            disabled={!isConnected}
          >
            Install Firmware Update
          </button>
        )}

        <div className="advanced-options">
          <h3>Advanced Options</h3>
          <div className="advanced-actions">
            <input 
              type="file" 
              accept=".zip"
              onChange={handleCustomFirmware}
              style={{ display: 'none' }}
              id="custom-firmware-input"
            />
            <button 
              className="button secondary"
              onClick={() => document.getElementById('custom-firmware-input')?.click()}
              disabled={!isConnected}
            >
              Load Custom Firmware
            </button>
            <button 
              className="button secondary danger"
              onClick={handleWipeBadge}
              disabled={!isConnected}
            >
              Wipe Badge
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
