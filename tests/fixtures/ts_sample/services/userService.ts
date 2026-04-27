import { Config } from '../config';

interface User {
    id: number;
    name: string;
}

export class UserService {
    private config: Config;

    constructor(config: Config) {
        this.config = config;
    }

    getAll(): User[] {
        return [
            { id: 1, name: 'Alice' },
            { id: 2, name: 'Bob' },
        ];
    }

    getById(id: number): User | undefined {
        return this.getAll().find(u => u.id === id);
    }
}

export const createService = (config: Config): UserService => {
    return new UserService(config);
};
