import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../utils/theme.dart';
import '../../models/message.dart';
import '../../providers/chat_provider.dart';

/// 聊天页面 — 参考 Replika 流畅动画风格
/// 
/// 使用 Riverpod 管理状态，确保切换页面后聊天记录不会丢失
class ChatScreen extends ConsumerStatefulWidget {
  final int? conversationId;
  
  const ChatScreen({
    super.key,
    this.conversationId,
  });

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> with TickerProviderStateMixin {
  final TextEditingController _ctrl = TextEditingController();
  final ScrollController _scrollCtrl = ScrollController();
  final List<AnimationController> _messageAnimations = [];

  @override
  void initState() {
    super.initState();
    // 初始化会话：如果有传入 conversationId 则加载，否则使用已保存的或创建新会话
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeSession();
    });
  }

  Future<void> _initializeSession() async {
    final notifier = ref.read(chatSessionProvider.notifier);
    await notifier.initializeSession(conversationId: widget.conversationId);
    await notifier.loadSuggestions();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _scrollCtrl.dispose();
    for (var c in _messageAnimations) {
      c.dispose();
    }
    super.dispose();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOutCubic,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;

    _ctrl.clear();
    
    final notifier = ref.read(chatSessionProvider.notifier);
    await notifier.sendMessage(text);
    
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatSessionProvider);
    
    // 当消息列表变化时滚动到底部
    ref.listen(chatSessionProvider, (previous, next) {
      if (previous?.messages.length != next.messages.length) {
        _scrollToBottom();
      }
    });

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: const Text('晚星'),
        actions: [
          _AnimatedIconButton(
            icon: Icons.phone_outlined,
            onTap: () {},
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          // 加载指示器
          if (chatState.isLoading)
            const LinearProgressIndicator(
              backgroundColor: Colors.transparent,
              valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primary),
            ),
          // 错误提示
          if (chatState.error != null)
            Container(
              padding: const EdgeInsets.all(12),
              color: AppTheme.danger.withOpacity(0.1),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: AppTheme.danger, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      chatState.error!,
                      style: TextStyle(color: AppTheme.danger, fontSize: 12),
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      ref.read(chatSessionProvider.notifier).clearError();
                      _initializeSession();
                    },
                    child: const Text('重试', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
            ),
          // 消息列表
          Expanded(
            child: _buildMessageList(chatState),
          ),
          // 快捷操作
          if (chatState.messages.length <= 4 && chatState.suggestions.isNotEmpty)
            _QuickActions(
              actions: chatState.suggestions,
              onTap: (text) {
                _ctrl.text = text;
                _sendMessage();
              },
            ),
          // 输入框
          _ChatInput(
            controller: _ctrl,
            onSend: _sendMessage,
            isLoading: chatState.isSending,
          ),
        ],
      ),
    );
  }

  Widget _buildMessageList(ChatSessionState chatState) {
    final messages = chatState.messages;
    
    if (messages.isEmpty && !chatState.isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.chat_bubble_outline,
              size: 64,
              color: AppTheme.muted.withOpacity(0.5),
            ),
            const SizedBox(height: 16),
            Text(
              '开始和晚星聊天吧',
              style: TextStyle(
                color: AppTheme.muted.withOpacity(0.7),
                fontSize: 16,
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 16),
      itemCount: messages.length + (chatState.showTyping ? 1 : 0),
      itemBuilder: (context, index) {
        // 正在输入指示器
        if (index == messages.length && chatState.showTyping) {
          return _TypingIndicator();
        }
        
        final msg = messages[index];
        return _MessageBubble(
          message: msg,
          animationDelay: index * 30,
        );
      },
    );
  }
}

/// 消息气泡（带动画）
class _MessageBubble extends StatefulWidget {
  final Message message;
  final int animationDelay;

  const _MessageBubble({
    required this.message,
    this.animationDelay = 0,
  });

  @override
  State<_MessageBubble> createState() => _MessageBubbleState();
}

class _MessageBubbleState extends State<_MessageBubble>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 350),
      vsync: this,
    );
    
    // 延迟启动动画
    Future.delayed(Duration(milliseconds: widget.animationDelay), () {
      if (mounted) {
        _controller.forward();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isUser = widget.message.isFromUser;

    Widget bubble;
    if (isUser) {
      // 用户消息 - 右对齐
      bubble = Align(
        alignment: Alignment.centerRight,
        child: ConstrainedBox(
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.72,
          ),
          child: Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: AppTheme.userBubbleDecoration,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  widget.message.content,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  _fmt(widget.message.createdAt),
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.72),
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    } else {
      // AI消息 - 左对齐
      bubble = Align(
        alignment: Alignment.centerLeft,
        child: ConstrainedBox(
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.72,
          ),
          child: Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: AppTheme.aiBubbleDecoration,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.message.content,
                  style: const TextStyle(
                    color: AppTheme.aiBubbleText,
                    fontSize: 14,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 5),
                Align(
                  alignment: Alignment.centerRight,
                  child: Text(
                    _fmt(widget.message.createdAt),
                    style: const TextStyle(
                      color: Color(0xFF777B8E),
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    // 进入动画
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Opacity(
          opacity: CurvedAnimation(
            parent: _controller,
            curve: Curves.easeOut,
          ).value,
          child: Transform.translate(
            offset: Offset(
              isUser ? 20 * (1 - _controller.value) : -20 * (1 - _controller.value),
              8 * (1 - _controller.value),
            ),
            child: child,
          ),
        );
      },
      child: bubble,
    );
  }

  String _fmt(DateTime t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
}

/// 带动画的图标按钮
class _AnimatedIconButton extends StatefulWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _AnimatedIconButton({required this.icon, required this.onTap});

  @override
  State<_AnimatedIconButton> createState() => _AnimatedIconButtonState();
}

class _AnimatedIconButtonState extends State<_AnimatedIconButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _controller.forward(),
      onTapUp: (_) {
        _controller.reverse();
        widget.onTap();
      },
      onTapCancel: () => _controller.reverse(),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: 1 - (_controller.value * 0.1),
            child: Container(
              width: 38,
              height: 38,
              decoration: AppTheme.iconButtonDecoration,
              alignment: Alignment.center,
              child: Icon(widget.icon, size: 18, color: AppTheme.muted),
            ),
          );
        },
      ),
    );
  }
}

/// 正在输入指示器（带伴侣小头像）
class _TypingIndicator extends StatefulWidget {
  @override
  State<_TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<_TypingIndicator>
    with TickerProviderStateMixin {
  late List<AnimationController> _dotControllers;

  @override
  void initState() {
    super.initState();
    _dotControllers = List.generate(3, (index) {
      return AnimationController(
        duration: const Duration(milliseconds: 600),
        vsync: this,
      );
    });

    for (int i = 0; i < 3; i++) {
      Future.delayed(Duration(milliseconds: i * 200), () {
        if (mounted) {
          _dotControllers[i].repeat(reverse: true);
        }
      });
    }
  }

  @override
  void dispose() {
    for (var c in _dotControllers) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: AppTheme.aiBubbleDecoration,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: List.generate(3, (index) {
                return AnimatedBuilder(
                  animation: _dotControllers[index],
                  builder: (context, child) {
                    return Container(
                      margin: const EdgeInsets.symmetric(horizontal: 2.5),
                      width: 7,
                      height: 7 + (_dotControllers[index].value * 5),
                      decoration: BoxDecoration(
                        color: AppTheme.aiBubbleText.withOpacity(0.5),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    );
                  },
                );
              }),
            ),
          ),
        ],
      ),
    );
  }
}

/// 快捷操作
class _QuickActions extends StatelessWidget {
  final List<String> actions;
  final Function(String) onTap;

  const _QuickActions({required this.actions, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: actions.map((text) {
          return _AnimatedChip(
            text: text,
            onTap: () => onTap(text),
          );
        }).toList(),
      ),
    );
  }
}

/// 带动画的芯片按钮
class _AnimatedChip extends StatefulWidget {
  final String text;
  final VoidCallback onTap;

  const _AnimatedChip({required this.text, required this.onTap});

  @override
  State<_AnimatedChip> createState() => _AnimatedChipState();
}

class _AnimatedChipState extends State<_AnimatedChip>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _controller.forward(),
      onTapUp: (_) {
        _controller.reverse();
        widget.onTap();
      },
      onTapCancel: () => _controller.reverse(),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: 1 - (_controller.value * 0.05),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0x14FFFFFF),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.line),
              ),
              child: Text(
                widget.text,
                style: const TextStyle(fontSize: 13, color: AppTheme.text),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// 聊天输入框
class _ChatInput extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  final bool isLoading;

  const _ChatInput({
    required this.controller,
    required this.onSend,
    required this.isLoading,
  });

  @override
  Widget build(BuildContext context) {
    final bottomPadding = MediaQuery.of(context).padding.bottom;
    return Container(
      padding: EdgeInsets.fromLTRB(18, 10, 18, 12 + bottomPadding),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              style: const TextStyle(color: AppTheme.text, fontSize: 14),
              decoration: InputDecoration(
                hintText: '输入消息...',
                suffixIcon: Padding(
                  padding: const EdgeInsets.only(right: 4),
                  child: Container(
                    decoration: AppTheme.iconButtonDecoration,
                    child: IconButton(
                      icon: const Icon(Icons.mic_outlined, size: 18),
                      onPressed: () {},
                    ),
                  ),
                ),
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onSend(),
            ),
          ),
          const SizedBox(width: 10),
          _SendButton(
            onTap: isLoading ? null : onSend,
            isLoading: isLoading,
          ),
        ],
      ),
    );
  }
}

/// 发送按钮
class _SendButton extends StatefulWidget {
  final VoidCallback? onTap;
  final bool isLoading;

  const _SendButton({this.onTap, required this.isLoading});

  @override
  State<_SendButton> createState() => _SendButtonState();
}

class _SendButtonState extends State<_SendButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: widget.onTap != null ? (_) => _controller.forward() : null,
      onTapUp: widget.onTap != null
          ? (_) {
              _controller.reverse();
              widget.onTap!();
            }
          : null,
      onTapCancel: widget.onTap != null ? () => _controller.reverse() : null,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: 1 - (_controller.value * 0.1),
            child: Container(
              width: 46,
              height: 46,
              decoration: AppTheme.primaryButtonDecoration,
              alignment: Alignment.center,
              child: widget.isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.send, color: Colors.white, size: 20),
            ),
          );
        },
      ),
    );
  }
}
