enum UserRole { mentor, mentee }

extension UserRoleX on UserRole {
  String get apiValue => this == UserRole.mentor ? 'mentor' : 'mentee';

  String get titleRu => this == UserRole.mentor ? 'Ментор' : 'Менти';

  static UserRole fromApi(String value) {
    return value == 'mentor' ? UserRole.mentor : UserRole.mentee;
  }
}

class User {
  final int id;
  final String firstName;
  final int age;
  final String description;
  final UserRole role;
  final String direction;
  final String? photoUrl;
  final bool isActive;

  const User({
    required this.id,
    required this.firstName,
    required this.age,
    required this.description,
    required this.role,
    required this.direction,
    required this.photoUrl,
    required this.isActive,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      firstName: (json['first_name'] ?? '') as String,
      age: (json['age'] ?? 0) as int,
      description: (json['description'] ?? '') as String,
      role: UserRoleX.fromApi((json['role'] ?? 'mentee') as String),
      direction: (json['direction'] ?? '') as String,
      photoUrl: json['photo_url'] as String?,
      isActive: (json['is_active'] ?? false) as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'first_name': firstName,
      'age': age,
      'description': description,
      'role': role.apiValue,
      'direction': direction,
      'photo_url': photoUrl,
      'is_active': isActive,
    };
  }
}

class CreateUserRequest {
  final String firstName;
  final int age;
  final String description;
  final UserRole role;
  final String direction;

  const CreateUserRequest({
    required this.firstName,
    required this.age,
    required this.description,
    required this.role,
    required this.direction,
  });

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'first_name': firstName,
      'age': age.toString(),
      'description': description,
      'role': role.apiValue,
      'direction': direction,
    };
  }
}

class UpdateUserRequest {
  final String? firstName;
  final int? age;
  final String? description;
  final UserRole? role;
  final String? direction;

  const UpdateUserRequest({
    this.firstName,
    this.age,
    this.description,
    this.role,
    this.direction,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = <String, dynamic>{};
    if (firstName != null) data['first_name'] = firstName;
    if (age != null) data['age'] = age.toString();
    if (description != null) data['description'] = description;
    if (role != null) data['role'] = role!.apiValue;
    if (direction != null) data['direction'] = direction;
    return data;
  }
}
