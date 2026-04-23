import 'package:flutter/material.dart';

import '../models/user.dart';

class CandidateCard extends StatelessWidget {
  const CandidateCard({
    super.key,
    required this.user,
    required this.photoUrl,
    required this.onLike,
    required this.onReport,
    required this.onDislike,
    required this.isBusy,
  });

  final User user;
  final String? photoUrl;
  final VoidCallback onLike;
  final VoidCallback onReport;
  final VoidCallback onDislike;
  final bool isBusy;

  static const Color _textColor = Color(0xFF555B6E);
  static const Color _cardColor = Color(0xFFDDF0EB);
  static const Color _likeColor = Color(0xFFC27D7D);
  static const Color _dislikeColor = Color(0xFFC27D7D);
  static const Color _reportColor = Color(0xFF9E9A2E);

  String get _roleLabel =>
      user.role == UserRole.mentor ? 'МЕНТОР' : 'МЕНТИ';

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        Container(
          decoration: BoxDecoration(
            color: _cardColor,
            borderRadius: BorderRadius.circular(28),
            boxShadow: const <BoxShadow>[
              BoxShadow(
                color: Color(0x25000000),
                blurRadius: 10,
                offset: Offset(0, 4),
              ),
            ],
          ),
          clipBehavior: Clip.antiAlias,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              AspectRatio(
                aspectRatio: 0.95,
                child: Stack(
                  fit: StackFit.expand,
                  children: <Widget>[
                    if (photoUrl != null)
                      Image.network(
                        photoUrl!,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => const ColoredBox(
                          color: Color(0xFFBEE3DB),
                          child: Icon(Icons.person, size: 72, color: _textColor),
                        ),
                      )
                    else
                      const ColoredBox(
                        color: Color(0xFFBEE3DB),
                        child: Icon(Icons.person, size: 72, color: _textColor),
                      ),
                    // Плавный градиент делает фото прозрачнее к низу,
                    // чтобы текстовый блок визуально читался как на макете.
                    const DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: <Color>[
                            Color(0x00000000),
                            Color(0x55DDF0EB),
                            _cardColor,
                          ],
                          stops: <double>[0.45, 0.75, 1.0],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            '${user.firstName}, ${user.age}',
                            style: const TextStyle(
                              color: _textColor,
                              fontSize: 38,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        Text(
                          _roleLabel,
                          style: const TextStyle(
                            color: _textColor,
                            fontSize: 24,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                    Text(
                      user.direction,
                      style: const TextStyle(
                        color: _textColor,
                        fontSize: 20,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Divider(color: _textColor, thickness: 1),
                    const SizedBox(height: 12),
                    Text(
                      user.description,
                      style: const TextStyle(
                        color: _textColor,
                        fontSize: 18,
                        height: 1.25,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: <Widget>[
            _actionButton(
              icon: Icons.favorite,
              color: _likeColor,
              onPressed: isBusy ? null : onLike,
            ),
            _actionButton(
              icon: Icons.shield,
              color: _reportColor,
              onPressed: isBusy ? null : onReport,
            ),
            _actionButton(
              icon: Icons.heart_broken,
              color: _dislikeColor,
              onPressed: isBusy ? null : onDislike,
            ),
          ],
        ),
      ],
    );
  }

  Widget _actionButton({
    required IconData icon,
    required Color color,
    required VoidCallback? onPressed,
  }) {
    return SizedBox(
      width: 84,
      height: 84,
      child: Material(
        color: const Color(0xFFDDF0EB),
        shape: const CircleBorder(),
        child: IconButton(
          onPressed: onPressed,
          iconSize: 42,
          splashRadius: 36,
          color: onPressed == null ? color.withValues(alpha: 0.4) : color,
          icon: Icon(icon),
        ),
      ),
    );
  }
}
