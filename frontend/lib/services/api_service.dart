import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../models/user.dart';
import 'telegram_init_data.dart';

class ApiException implements Exception {
  ApiException({
    required this.statusCode,
    required this.message,
    this.fieldErrors = const <String, String>{},
  });

  final int statusCode;
  final String message;
  final Map<String, String> fieldErrors;

  @override
  String toString() => message;
}

class ApiService {
  ApiService({String? baseUrl, String? telegramInitData})
    : _baseUrl =
          baseUrl ??
          const String.fromEnvironment(
            'API_BASE_URL',
            defaultValue: 'http://127.0.0.1:8000',
          ),
      _telegramInitData = telegramInitData ?? getTelegramInitData();

  final String _baseUrl;
  final String _telegramInitData;

  Map<String, String> get _headers => <String, String>{
    'X-Telegram-Init-Data': _telegramInitData,
  };

  Uri _uri(String path) => Uri.parse('$_baseUrl$path');

  Future<User?> getProfile() async {
    final http.Response response = await http.get(
      _uri('/api/users/me'),
      headers: _headers,
    );

    if (response.statusCode == 404) return null;
    _ensureSuccess(response);
    return User.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<User> createProfile(Map<String, dynamic> data, File? photo) async {
    final http.MultipartRequest request =
        http.MultipartRequest('POST', _uri('/api/users'))
          ..headers.addAll(_headers)
          ..fields.addAll(
            data.map(
              (dynamic k, dynamic v) => MapEntry(k.toString(), v.toString()),
            ),
          );

    if (photo != null) {
      request.files.add(await http.MultipartFile.fromPath('photo', photo.path));
    }

    final http.StreamedResponse streamed = await request.send();
    final http.Response response = await http.Response.fromStream(streamed);
    _ensureSuccess(response);
    return User.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<User> updateProfile(Map<String, dynamic> data, File? photo) async {
    final http.MultipartRequest request =
        http.MultipartRequest('PUT', _uri('/api/users/me'))
          ..headers.addAll(_headers)
          ..fields.addAll(
            data.map(
              (dynamic k, dynamic v) => MapEntry(k.toString(), v.toString()),
            ),
          );

    if (photo != null) {
      request.files.add(await http.MultipartFile.fromPath('photo', photo.path));
    }

    final http.StreamedResponse streamed = await request.send();
    final http.Response response = await http.Response.fromStream(streamed);
    _ensureSuccess(response);
    return User.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<bool> toggleActive() async {
    final http.Response response = await http.patch(
      _uri('/api/users/me/toggle-active'),
      headers: _headers,
    );
    _ensureSuccess(response);
    final Map<String, dynamic> body =
        jsonDecode(response.body) as Map<String, dynamic>;
    return (body['is_active'] ?? false) as bool;
  }

  void _ensureSuccess(http.Response response) {
    final int code = response.statusCode;
    if (code >= 200 && code < 300) {
      return;
    }

    String detail = 'Ошибка запроса ($code)';
    final Map<String, String> fieldErrors = <String, String>{};

    try {
      final Map<String, dynamic> body =
          jsonDecode(response.body) as Map<String, dynamic>;

      final dynamic responseDetail = body['detail'];
      if (responseDetail is String) {
        detail = responseDetail;
      } else if (responseDetail is List) {
        // Формат FastAPI/Pydantic для 422: список объектов с loc/msg.
        for (final dynamic entry in responseDetail) {
          if (entry is! Map<String, dynamic>) continue;
          final dynamic rawLoc = entry['loc'];
          final String msg = (entry['msg'] ?? 'Некорректное значение')
              .toString();
          if (rawLoc is List && rawLoc.isNotEmpty) {
            final String field = rawLoc.last.toString();
            fieldErrors[field] = msg;
          }
        }
        if (fieldErrors.isNotEmpty) {
          detail = 'Проверьте корректность заполнения полей.';
        }
      } else if (responseDetail != null) {
        detail = responseDetail.toString();
      }
    } catch (_) {
      // Если ответ не JSON, оставляем стандартное сообщение.
    }

    throw ApiException(
      statusCode: code,
      message: detail,
      fieldErrors: fieldErrors,
    );
  }
}
