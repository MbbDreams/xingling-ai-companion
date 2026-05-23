import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/secure_storage.dart';

/// API 配置
class ApiConfig {
  // 开发环境使用 localhost，生产环境需要改为实际服务器地址
  static const String baseUrl = 'http://localhost:8000/api/v1';
  static const Duration timeout = Duration(seconds: 30);
}

/// Dio 实例 Provider
final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.timeout,
      receiveTimeout: ApiConfig.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );

  // 添加 Token 拦截器
  dio.interceptors.add(AuthInterceptor());

  // 添加日志拦截器（调试用）
  dio.interceptors.add(LogInterceptor(
    requestBody: true,
    responseBody: true,
    error: true,
  ));

  // 添加错误处理拦截器
  dio.interceptors.add(InterceptorsWrapper(
    onError: (DioException error, ErrorInterceptorHandler handler) {
      // 统一错误处理
      String message = '网络错误';
      if (error.response != null) {
        final data = error.response?.data;
        if (data is Map && data.containsKey('detail')) {
          message = data['detail'];
        }
        // 处理 401 错误 - Token 过期
        if (error.response?.statusCode == 401) {
          message = '登录已过期，请重新登录';
        }
      } else if (error.type == DioExceptionType.connectionTimeout) {
        message = '连接超时，请检查网络';
      } else if (error.type == DioExceptionType.receiveTimeout) {
        message = '接收数据超时';
      }
      
      error = DioException(
        requestOptions: error.requestOptions,
        error: message,
        type: error.type,
        response: error.response,
      );
      
      handler.next(error);
    },
  ));

  return dio;
});

/// 认证拦截器 - 自动添加 JWT Token
class AuthInterceptor extends Interceptor {
  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (!_isAuthEndpoint(options.path)) {
      final token = await SecureStorage.getAccessToken();
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }
    handler.next(options);
  }

  /// 判断是否为认证相关接口（不需要 Token）
  bool _isAuthEndpoint(String path) {
    final authEndpoints = [
      '/auth/send-code',
      '/auth/register',
      '/auth/login',
      '/auth/refresh',
    ];
    return authEndpoints.any((endpoint) => path.contains(endpoint));
  }
}

/// API 服务基类
class ApiService {
  final Dio _dio;

  ApiService(this._dio);

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    return _dio.get<T>(path, queryParameters: queryParameters);
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) async {
    return _dio.post<T>(path, data: data, queryParameters: queryParameters);
  }

  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) async {
    return _dio.put<T>(path, data: data, queryParameters: queryParameters);
  }

  Future<Response<T>> delete<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    return _dio.delete<T>(path, queryParameters: queryParameters);
  }
}

/// API Service Provider
final apiServiceProvider = Provider<ApiService>((ref) {
  final dio = ref.watch(dioProvider);
  return ApiService(dio);
});

/// API 错误类型
enum ApiErrorType {
  network,
  server,
  notFound,
  unauthorized,
  badRequest,
  unknown,
}

/// API 异常
class ApiException implements Exception {
  final String message;
  final ApiErrorType type;
  final int? statusCode;

  ApiException({
    required this.message,
    this.type = ApiErrorType.unknown,
    this.statusCode,
  });

  @override
  String toString() => message;
}
