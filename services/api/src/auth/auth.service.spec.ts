import { Test, TestingModule } from '@nestjs/testing';
import { AuthService } from './auth.service';
import { PrismaService } from '../prisma/prisma.service';
import { JwtService } from '@nestjs/jwt';
import { compare } from 'bcrypt';

jest.mock('bcrypt', () => ({
  compare: jest.fn(),
  hash: jest.fn().mockResolvedValue('hashed_password'),
}));

const mockPrismaService = {
  usuario: {
    findUnique: jest.fn(),
    create: jest.fn(),
  },
};

const mockJwtService = {
  sign: jest.fn().mockReturnValue('test_token'),
};

describe('AuthService', () => {
  let service: AuthService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AuthService,
        { provide: PrismaService, useValue: mockPrismaService },
        { provide: JwtService, useValue: mockJwtService },
      ],
    }).compile();

    service = module.get<AuthService>(AuthService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('validateUser', () => {
    it('should return user data if validation is successful', async () => {
      const user = { id: '1', email: 'test@test.com', password: 'hashed_password' };
      mockPrismaService.usuario.findUnique.mockResolvedValue(user);
      (compare as jest.Mock).mockResolvedValue(true);

      const result = await service.validateUser('test@test.com', 'password');
      expect(result).toEqual({ id: '1', email: 'test@test.com' });
    });

    it('should return null if user is not found', async () => {
      mockPrismaService.usuario.findUnique.mockResolvedValue(null);
      const result = await service.validateUser('test@test.com', 'password');
      expect(result).toBeNull();
    });

    it('should return null if password does not match', async () => {
        const user = { id: '1', email: 'test@test.com', password: 'hashed_password' };
        mockPrismaService.usuario.findUnique.mockResolvedValue(user);
        (compare as jest.Mock).mockResolvedValue(false);

        const result = await service.validateUser('test@test.com', 'wrong_password');
        expect(result).toBeNull();
    });
  });

  describe('login', () => {
    it('should return an access token', () => {
      const user = { id: '1', email: 'test@test.com', role: 'ADMIN' };
      const result = service.login(user);
      expect(result).toEqual({ access_token: 'test_token' });
      expect(mockJwtService.sign).toHaveBeenCalledWith({ email: user.email, sub: user.id, role: user.role });
    });
  });
});
