import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/user.dart';
import '../services/api_service.dart';
import '../services/directions_service.dart';

class ProfileFormScreen extends StatefulWidget {
  const ProfileFormScreen({super.key, required this.apiService});

  final ApiService apiService;

  @override
  State<ProfileFormScreen> createState() => _ProfileFormScreenState();
}

class _ProfileFormScreenState extends State<ProfileFormScreen> {
  static const Color _bgColor = Color(0xFF89B0AE);
  static const Color _textColor = Color(0xFF555B6E);
  static const Color _buttonColor = Color(0xFFBEE3DB);
  static const Color _fieldColor = Color(0xFFD3D0CB);

  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _ageController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();

  UserRole _role = UserRole.mentee;
  String? _direction;
  bool _isLoading = true;
  bool _isSubmitting = false;
  bool _isEditMode = false;
  bool _isActive = true;
  String? _existingPhotoUrl;
  File? _pickedPhoto;
  final Map<String, String> _serverFieldErrors = <String, String>{};

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _ageController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    try {
      final User? user = await widget.apiService.getProfile();
      if (!mounted) return;
      if (user == null) {
        setState(() {
          _isEditMode = false;
          _isLoading = false;
          _direction = DirectionsService.directions.first;
        });
        return;
      }

      setState(() {
        _isEditMode = true;
        _isActive = user.isActive;
        _existingPhotoUrl = user.photoUrl;
        _nameController.text = user.firstName;
        _ageController.text = user.age.toString();
        _descriptionController.text = user.description;
        _role = user.role;
        _direction = user.direction.isEmpty
            ? DirectionsService.directions.first
            : user.direction;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      _showSnack('Ошибка загрузки профиля: $e');
    }
  }

  Future<void> _pickPhoto() async {
    final ImagePicker picker = ImagePicker();
    final XFile? picked = await showModalBottomSheet<XFile>(
      context: context,
      backgroundColor: Colors.white,
      builder: (BuildContext context) {
        return SafeArea(
          child: Wrap(
            children: <Widget>[
              ListTile(
                leading: const Icon(Icons.photo_camera_outlined),
                title: const Text('Сделать фото'),
                onTap: () async {
                  final XFile? file = await picker.pickImage(
                    source: ImageSource.camera,
                    imageQuality: 85,
                    maxWidth: 1200,
                  );
                  if (!context.mounted) return;
                  Navigator.of(context).pop(file);
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library_outlined),
                title: const Text('Выбрать из галереи'),
                onTap: () async {
                  final XFile? file = await picker.pickImage(
                    source: ImageSource.gallery,
                    imageQuality: 85,
                    maxWidth: 1200,
                  );
                  if (!context.mounted) return;
                  Navigator.of(context).pop(file);
                },
              ),
            ],
          ),
        );
      },
    );

    if (picked != null) {
      setState(() {
        _pickedPhoto = File(picked.path);
      });
    }
  }

  void _removePhoto() {
    setState(() {
      _pickedPhoto = null;
      _existingPhotoUrl = null;
    });
  }

  Future<void> _submit() async {
    setState(() => _serverFieldErrors.clear());
    if (!_formKey.currentState!.validate()) return;
    if (_direction == null || _direction!.isEmpty) {
      _showSnack('Выберите направление.');
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      final Map<String, dynamic> payload = <String, dynamic>{
        'first_name': _nameController.text.trim(),
        'age': int.parse(_ageController.text.trim()),
        'description': _descriptionController.text.trim(),
        'role': _role.apiValue,
        'direction': _direction!,
      };

      if (_isEditMode) {
        await widget.apiService.updateProfile(payload, _pickedPhoto);
      } else {
        await widget.apiService.createProfile(payload, _pickedPhoto);
      }
      if (!mounted) return;
      _showSnack(_isEditMode ? 'Анкета обновлена.' : 'Анкета создана.');
      await _loadProfile();
    } on ApiException catch (e) {
      if (!mounted) return;
      if ((e.statusCode == 400 || e.statusCode == 422) &&
          e.fieldErrors.isNotEmpty) {
        setState(() {
          _serverFieldErrors.addAll(e.fieldErrors);
        });
        _formKey.currentState!.validate();
      } else {
        _showSnack('Ошибка сохранения: ${e.message}');
      }
    } catch (e) {
      if (!mounted) return;
      _showSnack('Ошибка сохранения: $e');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  Future<void> _toggleActive() async {
    setState(() => _isSubmitting = true);
    try {
      final bool newStatus = await widget.apiService.toggleActive();
      if (!mounted) return;
      setState(() => _isActive = newStatus);
      _showSnack(newStatus ? 'Анкета снова отображается.' : 'Анкета скрыта.');
    } catch (e) {
      _showSnack('Ошибка переключения: $e');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  void _showSnack(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgColor,
      appBar: AppBar(
        backgroundColor: _bgColor,
        elevation: 0,
        title: Text(
          _isEditMode ? 'Редактирование анкеты' : 'Создание анкеты',
          style: const TextStyle(color: _textColor),
        ),
        iconTheme: const IconThemeData(color: _textColor),
        actions: <Widget>[
          if (_isEditMode)
            IconButton(
              tooltip: _isActive ? 'Скрыть анкету' : 'Показать анкету',
              onPressed: _isSubmitting ? null : _toggleActive,
              icon: Icon(_isActive ? Icons.visibility : Icons.visibility_off),
            ),
        ],
      ),
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : LayoutBuilder(
                builder: (BuildContext context, BoxConstraints constraints) {
                  final double w = constraints.maxWidth;
                  final double h = constraints.maxHeight;
                  final bool landscape = w > h;
                  final double horizontalPadding =
                      w * (landscape ? 0.16 : 0.06);
                  final double photoSize = landscape ? h * 0.30 : w * 0.38;
                  final double fieldRadius = 20;

                  return SingleChildScrollView(
                    padding: EdgeInsets.symmetric(
                      horizontal: horizontalPadding,
                      vertical: h * 0.02,
                    ),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: <Widget>[
                          SizedBox(height: h * 0.02),
                          Center(
                            child: Stack(
                              alignment: Alignment.center,
                              children: <Widget>[
                                CircleAvatar(
                                  radius: photoSize / 2,
                                  backgroundColor: _fieldColor,
                                  backgroundImage: _pickedPhoto != null
                                      ? FileImage(_pickedPhoto!)
                                      : (_existingPhotoUrl != null
                                            ? NetworkImage(
                                                    _resolvePhotoUrl(
                                                      _existingPhotoUrl!,
                                                    ),
                                                  )
                                                  as ImageProvider
                                            : null),
                                  child:
                                      (_pickedPhoto == null &&
                                          _existingPhotoUrl == null)
                                      ? Text(
                                          'Добавить фото',
                                          style: TextStyle(
                                            color: _textColor,
                                            fontSize: photoSize * 0.13,
                                          ),
                                        )
                                      : null,
                                ),
                                Positioned.fill(
                                  child: Material(
                                    color: Colors.transparent,
                                    child: InkWell(
                                      borderRadius: BorderRadius.circular(
                                        photoSize,
                                      ),
                                      onTap: _isSubmitting ? null : _pickPhoto,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          if (_pickedPhoto != null || _existingPhotoUrl != null)
                            TextButton(
                              onPressed: _isSubmitting ? null : _removePhoto,
                              child: const Text('Удалить фото'),
                            ),
                          SizedBox(height: h * 0.015),
                          _buildTextField(
                            controller: _nameController,
                            hint: 'Имя',
                            radius: fieldRadius,
                            validator: (String? value) =>
                                (value == null || value.trim().isEmpty)
                                ? 'Введите имя'
                                : null,
                          ),
                          SizedBox(height: h * 0.014),
                          _buildTextField(
                            controller: _ageController,
                            hint: 'Возраст',
                            radius: fieldRadius,
                            keyboardType: TextInputType.number,
                            validator: (String? value) {
                              final int? age = int.tryParse(value ?? '');
                              if (age == null) return 'Введите возраст';
                              if (age < 16 || age > 100) {
                                return 'Возраст должен быть от 16 до 100';
                              }
                              return null;
                            },
                          ),
                          SizedBox(height: h * 0.014),
                          _buildRoleSelector(),
                          SizedBox(height: h * 0.014),
                          _buildDirectionDropdown(fieldRadius),
                          SizedBox(height: h * 0.014),
                          _buildTextField(
                            controller: _descriptionController,
                            hint: 'О себе...',
                            radius: fieldRadius,
                            minLines: 6,
                            maxLines: 6,
                            validator: (String? value) {
                              final String text = (value ?? '').trim();
                              if (text.isEmpty) return 'Введите описание';
                              if (text.length < 10) {
                                return 'Минимум 10 символов';
                              }
                              return null;
                            },
                          ),
                          SizedBox(height: h * 0.025),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _buttonColor,
                              foregroundColor: _textColor,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(20),
                              ),
                              padding: EdgeInsets.symmetric(vertical: h * 0.02),
                              textStyle: TextStyle(
                                fontSize: h * 0.035,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            onPressed: _isSubmitting ? null : _submit,
                            child: _isSubmitting
                                ? SizedBox(
                                    width: h * 0.03,
                                    height: h * 0.03,
                                    child: const CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : Text(
                                    _isEditMode
                                        ? 'Сохранить изменения'
                                        : 'Создать анкету',
                                  ),
                          ),
                          SizedBox(height: h * 0.02),
                        ],
                      ),
                    ),
                  );
                },
              ),
      ),
    );
  }

  String _resolvePhotoUrl(String relativeUrl) {
    const String baseUrl = String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://127.0.0.1:8000',
    );
    if (relativeUrl.startsWith('http')) return relativeUrl;
    return '$baseUrl$relativeUrl';
  }

  Widget _buildRoleSelector() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: _fieldColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            'Роль',
            style: TextStyle(color: _textColor, fontWeight: FontWeight.w600),
          ),
          Row(
            children: <Widget>[
              Expanded(
                child: RadioListTile<UserRole>(
                  value: UserRole.mentor,
                  groupValue: _role,
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Text('Ментор', style: TextStyle(color: _textColor)),
                  onChanged: (UserRole? value) {
                    if (value != null) {
                      setState(() {
                        _role = value;
                        _serverFieldErrors.remove('role');
                      });
                    }
                  },
                ),
              ),
              Expanded(
                child: RadioListTile<UserRole>(
                  value: UserRole.mentee,
                  groupValue: _role,
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Text('Менти', style: TextStyle(color: _textColor)),
                  onChanged: (UserRole? value) {
                    if (value != null) {
                      setState(() {
                        _role = value;
                        _serverFieldErrors.remove('role');
                      });
                    }
                  },
                ),
              ),
            ],
          ),
          if (_serverFieldErrors['role'] != null)
            Padding(
              padding: const EdgeInsets.only(left: 12, bottom: 4),
              child: Text(
                _serverFieldErrors['role']!,
                style: const TextStyle(color: Colors.redAccent, fontSize: 12),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildDirectionDropdown(double radius) {
    return DropdownButtonFormField<String>(
      initialValue: _direction,
      decoration: InputDecoration(
        filled: true,
        fillColor: _fieldColor,
        hintText: 'Направление',
        hintStyle: TextStyle(color: _textColor.withValues(alpha: 0.85)),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radius),
          borderSide: BorderSide.none,
        ),
      ),
      items: DirectionsService.directions
          .map(
            (String item) =>
                DropdownMenuItem<String>(value: item, child: Text(item)),
          )
          .toList(),
      onChanged: (String? value) {
        setState(() {
          _direction = value;
          _serverFieldErrors.remove('direction');
        });
      },
      validator: (_) => _serverFieldErrors['direction'],
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String hint,
    required double radius,
    required String? Function(String?) validator,
    TextInputType? keyboardType,
    int minLines = 1,
    int maxLines = 1,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      minLines: minLines,
      maxLines: maxLines,
      style: TextStyle(color: _textColor),
      validator: validator,
      onChanged: (_) => setState(() {
        if (hint == 'Имя') _serverFieldErrors.remove('first_name');
        if (hint == 'Возраст') _serverFieldErrors.remove('age');
        if (hint == 'О себе...') _serverFieldErrors.remove('description');
      }),
      decoration: InputDecoration(
        filled: true,
        fillColor: _fieldColor,
        hintText: hint,
        hintStyle: TextStyle(color: _textColor.withValues(alpha: 0.85)),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radius),
          borderSide: BorderSide.none,
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radius),
          borderSide: const BorderSide(color: Colors.redAccent),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radius),
          borderSide: const BorderSide(color: Colors.redAccent),
        ),
        errorText: hint == 'Имя'
            ? _serverFieldErrors['first_name']
            : hint == 'Возраст'
            ? _serverFieldErrors['age']
            : hint == 'О себе...'
            ? _serverFieldErrors['description']
            : null,
      ),
    );
  }
}
