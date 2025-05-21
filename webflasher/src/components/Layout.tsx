import React from 'react';
import './Layout.css';

interface LayoutProps {
  leftPane: React.ReactNode;
  middlePane: React.ReactNode;
  rightPane: React.ReactNode;
}

export default function Layout({ leftPane, middlePane, rightPane }: LayoutProps) {
  return (
    <div className="layout">
      <div className="layout-pane left-pane">{leftPane}</div>
      <div className="layout-pane middle-pane">{middlePane}</div>
      <div className="layout-pane right-pane">{rightPane}</div>
    </div>
  );
}
