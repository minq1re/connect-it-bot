import 'user.dart';

class MatchItem {
  const MatchItem({
    required this.matchId,
    required this.partnerUserId,
    required this.partnerTelegramId,
    required this.partnerFirstName,
    required this.partnerAge,
    required this.partnerRole,
    required this.partnerDirection,
    required this.partnerPhotoUrl,
  });

  final int matchId;
  final int partnerUserId;
  final int partnerTelegramId;
  final String partnerFirstName;
  final int partnerAge;
  final UserRole partnerRole;
  final String partnerDirection;
  final String? partnerPhotoUrl;

  factory MatchItem.fromJson(Map<String, dynamic> json) {
    return MatchItem(
      matchId: (json['match_id'] ?? 0) as int,
      partnerUserId: (json['partner_user_id'] ?? 0) as int,
      partnerTelegramId: (json['partner_telegram_id'] ?? 0) as int,
      partnerFirstName: (json['partner_first_name'] ?? 'Пользователь') as String,
      partnerAge: (json['partner_age'] ?? 0) as int,
      partnerRole: UserRoleX.fromApi((json['partner_role'] ?? 'mentee') as String),
      partnerDirection: (json['partner_direction'] ?? '') as String,
      partnerPhotoUrl: json['partner_photo_url'] as String?,
    );
  }
}
