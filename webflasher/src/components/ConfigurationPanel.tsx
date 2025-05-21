import React from 'react';
import { useMicroPython } from '../MicroPythonContext';
import './ConfigurationPanel.css';

interface ConfigurationAttrs {
  userName: string;
  userHandle: string;
  userPronouns: string;
}

export default function ConfigurationPanel() {
  const { mp, isConnected } = useMicroPython();
  const [config, setConfig] = React.useState<ConfigurationAttrs>({
    userName: "",
    userPronouns: "",
    userHandle: "",
  });
  const [status, setStatus] = React.useState<string>("");

  React.useEffect(() => {
    if (isConnected && mp) {
      loadConfiguration();
    } else {
      setConfig({
        userName: "",
        userPronouns: "",
        userHandle: "",
      });
      setStatus("");
    }
  }, [isConnected, mp]);

  const loadConfiguration = async () => {
    if (!mp) return;

    try {
      setStatus("Loading configuration...");
      const configJson = await mp.downloadFileToString("/config.json");
      const savedConfig = JSON.parse(configJson);
      setConfig(savedConfig);
      setStatus("Configuration loaded");
      console.log("Loaded config:", savedConfig);
    } catch (error) {
      console.error("Failed to load configuration:", error);
      setStatus("No existing configuration found. Please save a new one.");
    }
  };

  const saveConfiguration = async () => {
    if (!mp) return;

    try {
      setStatus("Saving configuration...");
      await mp.uploadFile("/config.json", new TextEncoder().encode(JSON.stringify(config)));
      setStatus("Configuration saved");
      console.log("Saved config:", config);
    } catch (error) {
      console.error("Failed to save configuration:", error);
      setStatus("Failed to save configuration");
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setConfig(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="config-panel">
      <h2>Badge Configuration</h2>
      <div className="config-form">
        <div className="form-group">
          <label htmlFor="userName">Name</label>
          <input
            type="text"
            id="userName"
            name="userName"
            value={config.userName}
            onChange={handleChange}
            disabled={!isConnected}
          />
        </div>
        <div className="form-group">
          <label htmlFor="userHandle">Handle</label>
          <input
            type="text"
            id="userHandle"
            name="userHandle"
            value={config.userHandle}
            onChange={handleChange}
            disabled={!isConnected}
          />
        </div>
        <div className="form-group">
          <label htmlFor="userPronouns">Pronouns</label>
          <input
            type="text"
            id="userPronouns"
            name="userPronouns"
            value={config.userPronouns}
            onChange={handleChange}
            disabled={!isConnected}
          />
        </div>
      </div>
      {status && (
        <div className={`status-message ${status.includes("Failed") ? "error" : ""}`}>
          {status}
        </div>
      )}
      <div className="config-actions">
        <button 
          className="button primary"
          disabled={!isConnected}
          onClick={saveConfiguration}
        >
          Save Configuration
        </button>
      </div>
    </div>
  );
}
