import React from 'react';
import './HelpModal.css';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function HelpModal({ isOpen, onClose }: HelpModalProps) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>How to Use the Badge Flasher</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        
        <div className="modal-body">
          <section className="help-section">
            <h3>How to Use the Badge</h3>
            <ul>
              <li>If you're looking for how to use the badge itself, check out the <a href="https://github.com/mpkendall/shipwrecked-pcb/wiki" target="_blank" rel="noopener noreferrer">docs</a>.</li>
            </ul>
          </section>

          <section className="help-section">
            <h3>Getting Started</h3>
            <ol>
              <li>Connect your badge using the "Connect" button in the top-left</li>
              <li>The badge will show up as a "WebUSB" device - select it and click "Connect"</li>
              <li>Once connected, you can update firmware, configure your badge, and manage apps</li>
            </ol>
          </section>

          <section className="help-section">
            <h3>Firmware Updates</h3>
            <ol>
              <li>Click "Check for Updates" to see if new firmware is available</li>
              <li>If an update is found, click "Install Firmware Update" to install it</li>
              <li>Wait for the update to complete - don't disconnect your badge during this process</li>
            </ol>
          </section>

          <section className="help-section">
            <h3>Badge Configuration</h3>
            <ol>
              <li>Enter your name, pronouns, and Slack handle in the middle panel</li>
              <li>Click "Save Configuration" to save your changes to the badge</li>
              <li>Your information can then be seen in the 'Badge' app</li>
            </ol>
          </section>

          <section className="help-section">
            <h3>Managing Apps</h3>
            <ol>
              <li>The right panel shows all apps currently installed on your badge</li>
              <li>Click "Upload New App" to add a new app (a .zip file containing manifest.json, main.py, etc.)</li>
              <li>Use the "Delete" button next to an app to remove it</li>
            </ol>
          </section>

          <section className="help-section">
            <h3>Advanced Options</h3>
            <ul>
              <li><strong>Load Custom Firmware:</strong> Load a custom firmware package (usually a zipped version of Code/build)</li>
              <li><strong>Wipe Badge:</strong> Reset the badge to factory settings (removes all apps and settings)</li>
            </ul>
          </section>

          <section className="help-section">
            <h3>Troubleshooting</h3>
            <ul>
              <li>If the badge isn't connecting, try unplugging it and plugging it back in</li>
              <li>Make sure you're using a compatible browser (Chrome or Firefox with WebSerial add-on)</li>
              <li>If you're having issues, try wiping the badge and reinstalling the firmware</li>
            </ul>
          </section>
        </div>

        <div className="modal-footer">
          <button className="button primary" onClick={onClose}>Got it!</button>
        </div>
      </div>
    </div>
  );
}
