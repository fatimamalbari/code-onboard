import { UserService } from './services/userService';
import { Config } from './config';

const config = new Config();
const service = new UserService(config);

export function main(): void {
    const users = service.getAll();
    console.log(`Found ${users.length} users`);
}

main();
