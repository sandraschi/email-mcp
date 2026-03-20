import {
    Github,
    Bot,
    Archive
} from 'lucide-react';

export interface AppEntry {
    id: string;
    label: string;
    description: string;
    icon: any;
    url: string; // Absolute URL for cross-app navigation
    port: number;
    tags: string[];
}

// SOTA App Catalog - Single Source of Truth for Navigation
export const APPS_CATALOG: AppEntry[] = [
    {
        id: 'git-github',
        label: 'Git & GitHub',
        description: 'Repository management and version control',
        icon: Github,
        url: 'http://localhost:10702',
        port: 10702,
        tags: ['dev', 'scm']
    },
    {
        id: 'robotics',
        label: 'Robotics Control',
        description: 'Physical and virtual robot orchestration',
        icon: Bot,
        url: 'http://localhost:10706',
        port: 10706,
        tags: ['hardware', 'simulation']
    },
    {
        id: 'winrar',
        label: 'Archive Manager',
        description: 'File compression and extraction utilities',
        icon: Archive,
        url: 'http://localhost:10763',
        port: 10763,
        tags: ['utility', 'files']
    },
    // ... (Add other apps as they are upgraded)
];
