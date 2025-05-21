import { useMicroPython } from "../../MicroPythonContext";

export interface AppManifest {
    displayName: string;
    logoPath: string;
    appNumber: number;
}

export interface App {
    manifest: AppManifest;
    path: string;
}

interface AppListItemProps {
    app: App;
    onDelete: (app: App) => void;
    disabled?: boolean;
}

export default function AppListItem({ app, onDelete, disabled = false }: AppListItemProps) {
    const { manifest, path } = app;

    const handleDelete = () => {
        if (disabled) return;
        const confirmDelete = window.confirm(`Are you sure you want to delete ${manifest.displayName}?`);
        if (confirmDelete) {
            onDelete(app);
        }
    };

    return (
        <div className="app-item">
            <div className="app-info">
                <div className="app-name">{manifest.displayName}</div>
                <div className="app-details">
                    <span>App #{manifest.appNumber}</span>
                    <span>•</span>
                    <span>{manifest.logoPath}</span>
                </div>
                <div className="app-path">{path}</div>
            </div>
            <div className="app-actions">
                <button 
                    className="button secondary" 
                    onClick={handleDelete}
                    disabled={disabled}
                    title={disabled ? "Please wait for current operation to complete" : "Delete this app"}
                >
                    Delete
                </button>
            </div>
        </div>
    );
}
