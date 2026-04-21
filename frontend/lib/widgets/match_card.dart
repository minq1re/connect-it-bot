import 'package:flutter/material.dart';

import '../models/match_item.dart';
import '../models/user.dart';

class MatchCard extends StatelessWidget {
  const MatchCard({
    super.key,
    required this.item,
    required this.photoUrl,
    required this.onOpenChat,
  });

  final MatchItem item;
  final String? photoUrl;
  final VoidCallback onOpenChat;

  static const Color _cardColor = Color(0xFFBEE3DB);
  static const Color _textColor = Color(0xFF555B6E);

  @override
  Widget build(BuildContext context) {
    final String roleLabel =
        item.partnerRole == UserRole.mentor ? 'Ментор' : 'Менти';

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: _cardColor,
        borderRadius: BorderRadius.circular(24),
      ),
      clipBehavior: Clip.antiAlias,
      child: Row(
        children: <Widget>[
          SizedBox(
            width: 122,
            height: 122,
            child: Stack(
              fit: StackFit.expand,
              children: <Widget>[
                if (photoUrl != null)
                  Image.network(
                    photoUrl!,
                    fit: BoxFit.cover,
                    loadingBuilder: (
                      BuildContext context,
                      Widget child,
                      ImageChunkEvent? progress,
                    ) {
                      if (progress == null) return child;
                      return const ColoredBox(
                        color: Color(0xFFD3D0CB),
                        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
                      );
                    },
                    errorBuilder: (_, _, _) => const ColoredBox(
                      color: Color(0xFFD3D0CB),
                      child: Icon(Icons.person, color: _textColor, size: 42),
                    ),
                  )
                else
                  const ColoredBox(
                    color: Color(0xFFD3D0CB),
                    child: Icon(Icons.person, color: _textColor, size: 42),
                  ),
                // Плавный градиент для мягкого перехода фото к плашке карточки.
                const DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: <Color>[
                        Color(0x00000000),
                        Color(0x44BEE3DB),
                        Color(0xFFBEE3DB),
                      ],
                      stops: <double>[0.35, 0.72, 1.0],
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Text(
                    '${item.partnerFirstName}, ${item.partnerAge}',
                    style: const TextStyle(
                      color: _textColor,
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '$roleLabel · ${item.partnerDirection}',
                    style: const TextStyle(
                      color: _textColor,
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: TextButton.icon(
                      onPressed: onOpenChat,
                      icon: const Icon(Icons.chat_bubble_outline),
                      label: const Text('Написать'),
                      style: TextButton.styleFrom(
                        foregroundColor: _textColor,
                        backgroundColor: Colors.white.withValues(alpha: 0.45),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 8,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
