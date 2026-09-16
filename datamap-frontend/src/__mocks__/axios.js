const mockAxios = {
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: [] })),
  create: jest.fn(function () {
    return mockAxios;
  }),
};

export default mockAxios;
