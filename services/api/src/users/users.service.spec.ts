import { Test, TestingModule } from '@nestjs/testing';
import { UsersService } from './users.service';
import { PrismaService } from '../prisma/prisma.service';
import { ConflictException, NotFoundException } from '@nestjs/common';
import { UserRole } from '@prisma/client';

const mockPrismaService = {
  usuario: {
    findUnique: jest.fn(),
    create: jest.fn(),
    findMany: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  },
};

describe('UsersService', () => {
  let service: UsersService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UsersService,
        { provide: PrismaService, useValue: mockPrismaService },
      ],
    }).compile();

    service = module.get<UsersService>(UsersService);
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('create', () => {
    it('should create a new user', async () => {
      const dto = { name: 'Test', email: 'test@test.com', password: 'password', role: UserRole.ADMIN };
      const user = { id: '1', ...dto, password: 'hashed_password' };

      mockPrismaService.usuario.findUnique.mockResolvedValue(null);
      mockPrismaService.usuario.create.mockResolvedValue(user);

      const result = await service.create(dto);
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { password, ...expectedResult } = user;
      expect(result).toEqual(expectedResult);
    });

    it('should throw a ConflictException if email already exists', async () => {
        const dto = { name: 'Test', email: 'test@test.com', password: 'password', role: UserRole.ADMIN };
        mockPrismaService.usuario.findUnique.mockResolvedValue({ id: '1' });

        await expect(service.create(dto)).rejects.toThrow(ConflictException);
    });
  });

  describe('findOne', () => {
    it('should return a single user', async () => {
        const user = { id: '1', name: 'Test', email: 'test@test.com', password: 'hashed_password' };
        mockPrismaService.usuario.findUnique.mockResolvedValue(user);

        const result = await service.findOne('1');
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { password, ...expectedResult } = user;
        expect(result).toEqual(expectedResult);
    });

    it('should throw a NotFoundException if user is not found', async () => {
        mockPrismaService.usuario.findUnique.mockResolvedValue(null);
        await expect(service.findOne('1')).rejects.toThrow(NotFoundException);
    });
  });
});
